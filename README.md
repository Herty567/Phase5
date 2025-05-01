# Phase 5
Team members: Jacob Alicea, Josiah Concepcion, Jamie Oliphant, Tim Saari

Files: sender.py, receiver.py, plot_phase5_perf.py, plot_intransfer.py, experiment.py, utils.py, tiger.jpg

This phase implements a pipelined file transfer using the Go-Back-N (GBN) protocol over an unreliable UDP connection.

receiver.py: Listens for packets from the sender, checks for duplicates or corruption using checksums, and writes valid data to received_tiger.jpg. Sends ACKs for correctly received packets.

sender.py: Reads tiger.jpg in 1024-byte chunks, creates packets with sequence numbers and checksums, and sends them using a Go-Back-N pipeline. Simulates timeout and loss. Logs RTT, cwnd, and RTO to tcp_timeseries.csv.

tiger.jpg: A 1.1 MB image file used to test the transfer protocol and check for errors or loss.

experiment.py: Runs automated tests over different loss rates, timeouts, and window sizes. Saves performance data to phase5_perf.csv.

plot_phase5_perf.py: Creates graphs of transfer time vs. loss rate, timeout, and window size.

plot_intransfer.py: Graphs cwnd, RTT, and RTO over time using tcp_timeseries.csv.

How to run:

Start receiver.py first.

Then run sender.py with desired loss_rate, timeout, and init_window.

Use experiment.py to automate testing.

Use plot_phase5_perf.py and plot_intransfer.py to view performance results.

Language: Python
IDE: PyCharm (or any IDE that supports running multiple Python files)
