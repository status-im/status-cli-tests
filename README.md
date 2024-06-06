# status-cli-tests

Status cli tool tests with focus on reliability under [unreliable network conditions](https://github.com/status-im/status-go/issues/5144).

## Setup and contribute

Install python 3.12 (might work with other versions as well but was tested only with 3.12)

```shell
git clone git@github.com:status-im/status-cli-tests.git
cd status-cli-tests
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
(optional) Overwrite default vars from src/env_vars.py via cli env vars or by adding a .env file
pytest (for all test)
pytest -k "test_one_to_one_with_latency" (for single test)
``` 



## CI

- Test runs via github actions
<!-- - [Allure Test Reports](https://status-im.github.io/status-cli-tests/49/) are published via github pages -->

## License

Licensed and distributed under either of

- MIT license: [LICENSE-MIT](https://github.com/status-im/status-cli-tests/blob/master/LICENSE-MIT) or http://opensource.org/licenses/MIT

or

- Apache License, Version 2.0, ([LICENSE-APACHE-v2](https://github.com/status-im/status-cli-tests/blob/master/LICENSE-APACHE-v2) or http://www.apache.org/licenses/LICENSE-2.0)

at your option. These files may not be copied, modified, or distributed except according to those terms.
