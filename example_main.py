from overbuild import ImportHookConfig, install_import_hook

install_import_hook(
    config=ImportHookConfig(
        output_path="overbuild_report.json", # optional custom report path
        report_interval_seconds=10 * 60, # default: 10 minutes
    )
)

import sample_app.service as service


if __name__ == "__main__":
    service.run(True)
    service.run(False)
