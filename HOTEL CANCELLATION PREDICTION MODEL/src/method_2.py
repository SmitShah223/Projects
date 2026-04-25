import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Load the cleaned dataset
df = pd.read_csv('hotel_bookings_cleaned.csv')

#df = df.drop(['Days_in_waiting_list'], axis=1)

cols_to_replace = ['hotel_City Hotel', 'hotel_Resort Hotel', 'meal_deposit_BB_No Deposit', 'meal_deposit_FB_No Deposit', 'meal_deposit_HB_No Deposit', 'meal_deposit_SC_No Deposit', 'market_segment_Complementary', 'market_segment_Corporate', 'market_segment_Direct', 'market_segment_Offline TA/TO', 'market_segment_Online TA', 'distribution_channel_Corporate', 'distribution_channel_Direct', 'distribution_channel_GDS', 'distribution_channel_TA/TO', 'reserved_room_type_A', 'reserved_room_type_C', 'reserved_room_type_D', 'reserved_room_type_E', 'reserved_room_type_H', 'assigned_room_type_A', 'assigned_room_type_B', 'assigned_room_type_C', 'assigned_room_type_D', 'assigned_room_type_E', 'assigned_room_type_F', 'assigned_room_type_H', 'customer_type_Contract', 'customer_type_Group', 'customer_type_Transient', 'customer_type_Transient-Party']

df[cols_to_replace] = df[cols_to_replace].replace({True: 1, False: 0})

#X = df.drop(['is_canceled'], axis=1)
df = pd.get_dummies(df, columns=['country'])

# Extract day of the week, day of the year, and month as separate columns
df['arrival_date'] = pd.to_datetime(df['arrival_date'])
df['arrival_day_of_week'] = df['arrival_date'].dt.dayofweek
df['arrival_day_of_year'] = df['arrival_date'].dt.dayofyear
df['arrival_month'] = df['arrival_date'].dt.month

# Drop the original date column
df = df.drop('arrival_date', axis=1)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df.drop('is_canceled', axis=1), df['is_canceled'], test_size=0.2, random_state=42)

# Scale the numerical columns
scaler = StandardScaler()
numerical_cols = ['lead_time', 'stays_in_weekend_nights', 'stays_in_week_nights', 'adults', 'babies', 'previous_cancellations', 'previous_bookings_not_canceled', 'booking_changes', 'days_in_waiting_list', 'adr', 'required_car_parking_spaces', 'total_of_special_requests']
X_train[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])
X_test[numerical_cols] = scaler.transform(X_test[numerical_cols])

# Train a logistic regression model
clf = LogisticRegression(random_state=42)
clf.fit(X_train, y_train)

# Make predictions on the test set
y_pred = clf.predict(X_test)

# Evaluate the accuracy of the model
accuracy = accuracy_score(y_test, y_pred)
print('Accuracy:', accuracy)
