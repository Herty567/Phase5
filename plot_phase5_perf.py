import pandas as pd
import matplotlib.pyplot as plt

# 1) Load the CSV
df = pd.read_csv("phase5_perf.csv")

# 2) Completion Time vs Loss Rate
df_loss = df.groupby("loss_rate")["duration"].mean().reset_index()
plt.figure()
plt.plot(df_loss["loss_rate"], df_loss["duration"], marker="o")
plt.xlabel("Loss Rate")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Loss Rate")
plt.grid(True)
plt.savefig("perf_vs_loss.png")

# 3) Completion Time vs Timeout Value
df_to = df.groupby("timeout")["duration"].mean().reset_index()
plt.figure()
plt.plot(df_to["timeout"], df_to["duration"], marker="o")
plt.xlabel("Timeout (s)")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Timeout Value")
plt.grid(True)
plt.savefig("perf_vs_timeout.png")

# 4) Completion Time vs Initial Window Size
df_win = df.groupby("init_window")["duration"].mean().reset_index()
plt.figure()
plt.plot(df_win["init_window"], df_win["duration"], marker="o")
plt.xlabel("Initial Window Size")
plt.ylabel("Completion Time (s)")
plt.title("Completion Time vs Initial Window Size")
plt.grid(True)
plt.savefig("perf_vs_init_window.png")
