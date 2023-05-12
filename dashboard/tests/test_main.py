from unittest import mock

import src.k8s
import src.main


class TestStartup:
    @mock.patch.object(src.main.uvicorn, "run")
    def test_main_default(self, m_uv):
        """Main function must setup UV loop with correct parameters."""
        # Main function must exist with code 0.
        assert src.main.main() == 0

        # Verify the call arguments to start the UV loop.
        assert m_uv.call_count == 1
        cargs = m_uv.call_args_list[0][1]
        assert cargs == {
            "app": src.server.FASTAPI_APP,
            "host": "0.0.0.0",
            "port": 8080,
            "log_level": "info",
            "access_log": False,
            "log_config": None,
        }

    def test_missing_k8s_env_vars(self):
        """Server must exit with error if any environment variables are missing."""
        with mock.patch.dict("os.environ", values={}, clear=True):
            assert src.main.main() == 1
