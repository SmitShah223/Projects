import pandas as pd
import numpy as np
import datetime

# Load the dataset
df = pd.read_csv('train.csv')

# Drop irrelevant columns
df = df.drop(['id', 'reservation_status', 'reservation_status_date'], axis=1)

# Merge date columns into a single datetime column
def month_name_to_number(name):
    date = datetime.datetime.strptime(name, "%B")
    return date.month
df['arrival_date_month'] = df['arrival_date_month'].apply(month_name_to_number)

df['arrival_date'] = pd.to_datetime(df['arrival_date_year'].astype(str) + '-' + df['arrival_date_month'].astype(str) + '-' + df['arrival_date_day_of_month'].astype(str), format='%Y-%m-%d')
df = df.drop(['arrival_date_year', 'arrival_date_month', 'arrival_date_day_of_month'], axis=1)

# Merge meal and deposit_type into a single categorical column
df['meal_deposit'] = df['meal'] + '_' + df['deposit_type']
df = df.drop(['meal', 'deposit_type'], axis=1)

# Clean the data
df = df.replace({'children': np.nan, 'country': np.nan, '': np.nan})  # Replace empty strings with NaN values
#df = df[~df['column_name'].str.match(r'^\s*$')]
df = df.dropna() # Drop rows with missing values

# Encode categorical columns
categorical_cols = ['hotel', 'meal_deposit', 'market_segment', 'distribution_channel', 'reserved_room_type', 'assigned_room_type', 'customer_type']
df = pd.get_dummies(df, columns=categorical_cols)

# Normalize numerical columns
numerical_cols = ['lead_time', 'stays_in_weekend_nights', 'stays_in_week_nights', 'adults', 'babies', 'previous_cancellations', 'previous_bookings_not_canceled', 'booking_changes', 'days_in_waiting_list', 'adr', 'required_car_parking_spaces', 'total_of_special_requests']
df[numerical_cols] = (df[numerical_cols] - df[numerical_cols].mean()) / df[numerical_cols].std()

# Convert the target column to binary
df['is_canceled'] = (df['is_canceled'] == 1).astype(int)

# Save the cleaned dataset to a new file
df.to_csv('hotel_bookings_cleaned.csv', index=False)
