# Transfer compatibility fix

Replace `transfer_plots.py` and `pages/5_Electricity_Transfers.py`, then reboot the deployed Streamlit app.

The page now calls the plotting helper with its original two arguments. This works with both the previous helper and the newer helper accepting `compact`. The month popover also no longer passes the optional width argument. Chart sizing is applied to the returned figure.

The old-helper compatibility test and transfer totals/style test passed with controlled data. This fixes those compatibility risks; the screenshot did not contain the final exception message, so the exact deployed TypeError has not been confirmed.

If it persists, open Manage app → logs and copy the final `TypeError: ...` line and the transfer-page line above it. The line in `analysis_popup.py` only launches the page; it does not identify the failed function.

This is separate from missing VASS weather data. Nothing in this ZIP changes MongoDB, local samples or region boundaries.
