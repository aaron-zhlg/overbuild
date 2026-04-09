from overbuild import install_import_hook
install_import_hook()

import sample_app.service as service


if __name__ == "__main__":
    service.run(True)
    service.run(False)
