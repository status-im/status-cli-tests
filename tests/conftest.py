# -*- coding: utf-8 -*-
import inspect
import glob
import shutil
from src.data_storage import DS
from src.libs.custom_logger import get_custom_logger
import os
import pytest
import src.env_vars as env_vars


logger = get_custom_logger(__name__)


# See https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
        return rep
    return None


@pytest.fixture(scope="session", autouse=True)
def set_allure_env_variables():
    yield
    if os.path.isdir("allure-results") and not os.path.isfile(os.path.join("allure-results", "environment.properties")):
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        with open(os.path.join("allure-results", "environment.properties"), "w") as outfile:
            for attribute_name in dir(env_vars):
                if attribute_name.isupper():
                    attribute_value = getattr(env_vars, attribute_name)
                    outfile.write(f"{attribute_name}={attribute_value}\n")


@pytest.fixture(scope="function", autouse=True)
def save_node_logs_on_fail(request, clear_open_nodes):
    yield
    if env_vars.RUNNING_IN_CI and hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        test_name = request.node.name.lower()
        class_name = request.node.cls.__name__.lower() if request.node.cls else ""
        logger.debug("Test failed, attempting to rename and move logs to the test_results folder")

        test_results_dir = "test_results"
        if not os.path.exists(test_results_dir):
            os.makedirs(test_results_dir)

        for file in glob.glob("*.log"):
            new_file_name = f"{class_name}_{test_name}_{os.path.basename(file)}"
            new_file_path = os.path.join(test_results_dir, new_file_name)
            shutil.move(file, new_file_path)
            logger.debug(f"Moved log file {file} to {new_file_path}")


@pytest.fixture(scope="function", autouse=True)
def clear_open_nodes():
    DS.nodes = []
    yield
    logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
    for node in DS.nodes:
        try:
            node.stop()
        except Exception as ex:
            logger.error(f"Failed to stop node because of error {ex}")
        node.clear_logs()
