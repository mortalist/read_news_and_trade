import matplotlib.pyplot as plt
from datetime import datetime

# 1. Your raw data: list[tuple(timestamp, price)]
raw_data = [
    ("2026-01-01 09:00", 150.25),
    ("2026-01-01 10:00", 152.50),
    ("2026-01-01 11:00", 149.10),
    ("2026-01-01 12:00", 155.00),
    ("2026-01-01 13:00", 153.75)
]

# 2. Extract and convert
# We convert the string timestamp into a datetime object for better spacing
dates = [datetime.strptime(item[0], "%Y-%m-%d %H:%M") for item in raw_data]
print(dates)
prices = [item[1] for item in raw_data]

# 3. Create the plot
plt.figure(figsize=(10, 5))
plt.plot(dates, prices, marker='o', linestyle='-', color='b')

# 4. Formatting the visuals
plt.title("Price Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Price ($)")
plt.grid(True)
plt.xticks(rotation=45) # Rotates labels so they don't overlap
plt.tight_layout()

# 5. Display
plt.show()