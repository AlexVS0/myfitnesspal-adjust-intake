# myfitnesspal-adjust_intake
A GUI application which calculates the user's real TDEE (total daily energy expenditure) based on their weight history input and matching MyFitnessPal intake records.
Written in Python 3.10.1.

Run this application to easily calculate your true energy expenditure instead of relying on calculators which make an (often inaccurate) estimate. 

#### Requires the following user input:

1. MyFitnessPal credentials (these will not be stored).
2. A log of your weight measurements (daily measurements taken at roughly the same time of the day is most accurate). The dates in the log will determine the date range on which the calculation will be run. The log should be a .csv or .txt file, with each row in the format DD/MM/YYYY, weight measurement (e.g. 10/02/2022, 73.8). In this initial release, no dates should be skipped, so for any dates with no measurement available, the measurement field/column should be left empty or as N/A.
3. Selection of your preferred measurement unit (kg or lbs).
4. Your desired rate of weight loss/gain per month, in your chosen unit. Choosing 0 will output your TDEE (maintenance calories) only.

#### Output

1. Average daily deficit/surplus.
2. Weekly rate of weight change.
3. Goal caloric intake to match the user's desired rate of weight change; maintenance intake (TDEE)
4. Flags when days in the selected date range lack caloric intake data on the user's MyFitnessPal diary.
5. Flags when more than 40% of days in the selected range lack weight measurements.
