"""Settings shared by every step of the project. Change values here to try new scenarios."""

# Clinic opening hours: 8:00 to 20:00, so 12 one-hour periods per day
OPEN_HOUR = 8
CLOSE_HOUR = 20
HOURS = list(range(OPEN_HOUR, CLOSE_HOUR))
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Patient service
SERVICE_MIN = 15          # average minutes a staff member spends with one patient
TARGET_UTILIZATION = 0.80 # plan staff so they are busy about 80% of the time

# Shift options the optimizer can choose from: length in hours -> cost per shift ($)
# Shorter shifts cost a bit more per hour (call-in premium).
HOURLY_WAGE = 32.0
SHIFTS = {4: 4 * HOURLY_WAGE * 1.10, 6: 6 * HOURLY_WAGE * 1.05, 8: 8 * HOURLY_WAGE}
MIN_STAFF = 1             # never leave the clinic empty while open

# History used for forecasting
WEEKS_OF_HISTORY = 12
RANDOM_SEED = 42

# Simulation
SIM_REPLICATIONS = 30     # how many simulated weeks to average over
WAIT_TARGET_MIN = 15      # service-level target: patients seen within 15 minutes

# What-if scenario: demand growth (e.g. a new clinic closes nearby)
SCENARIO_DEMAND_GROWTH = 0.20
