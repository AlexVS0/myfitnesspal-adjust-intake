import myfitnesspal
import tkinter as tk
import tkinter.filedialog
import tkinter.simpledialog
import tkinter.messagebox
from datetime import timedelta, datetime
import numpy as np


def getdaterange(start_date, end_date) -> list:
    """Returns a half-open range of dates (left-closed as per Python
    conventions) as a list of datetime.date objects for each day between
    start_date and end_date."""
    if start_date >= end_date:
        daterange_error = ValueError("The start date of a range" +
                                     " must precede the end date.")
        raise daterange_error
    daterange = []
    one_day = timedelta(1)
    rangewidth = end_date - start_date
    for number in range(rangewidth.days):
        daterange.append(start_date + number * one_day)
    return daterange


def get_weightdata() -> dict:
    """Prompts the user to select a .csv or .txt file containing
    comma-seperated values of dates (DD/MM/YYYY) and weight readings, and
    returns a dictionary with the dates as keys and the weight readings as
    values."""
    file_prompt_body = ("Please choose a .csv or .txt file containing your "
                        "weight record in the following format:"
                        "\nDD/MM/YYYY, weight reading 1"
                        "\nDD/MM/YYYY, weight reading 2"
                        "\nDD/MM/YYYY, weight reading 3\netc.\n"
                        "If no weight reading is available for a specific date"
                        ", keep the date entry but leave the weight reading "
                        "blank or write N/A.")
    file_prompt_title = "Choose your weight record data file"
    root = tk.Tk()
    root.withdraw()
    tkinter.messagebox.showinfo(file_prompt_title, file_prompt_body,
                                parent=root)
    root.destroy()
    root = tk.Tk()
    root.withdraw()
    weight_record = tkinter.filedialog.askopenfilename(title=file_prompt_title,
                                                       parent=root)
    root.destroy()
    f = open(weight_record, 'r')
    weightdata = {}
    for line in f.readlines():
        (day_str, reading) = (line.strip().split(","))
        try:
            day = datetime.strptime(day_str, '%d/%m/%Y').date()
        except ValueError:
            raise ValueError("Please ensure that the date column in your "
                             "file only contains dates in the format "
                             "DD/MM/YYYY or D/M/YYYY")
        try:
            weightdata[day] = float(reading)
        except (ValueError, TypeError):
            weightdata[day] = None
    return weightdata


class Mfp_range:
    def __init__(self,
                 start_date,
                 end_date,
                 client,
                 weight_data,
                 ismetric: bool):
        self.start_date = start_date
        self.end_date = end_date
        self.date_range = getdaterange(self.start_date, self.end_date)
        self.isblankestimate = False
        self.client = client
        self.weight_data = weight_data
        self.ismetric = ismetric
        self.weightdatacoverage = 0
        self.caloriedatacoverage = 0

    def calories(self) -> float:
        """Returns a sum of the caloric intake for the (half-open, left-closed)
        date range defined by the Mfp_range object. For any days with no data,
        caloric intake is estimated as an average of all other days."""
        caloriesum = 0
        incomplete_days = []
        for day in self.date_range:
            try:
                intake = self.client.get_date(day).totals['calories']
                if intake == 0:
                    incomplete_days.append(day)
                caloriesum += intake
            except KeyError:
                incomplete_days.append(day)
        if incomplete_days != []:
            # set estimation flag to True
            self.isblankestimate = True
            # for any days with no intake data, make an estimation of the
            # intake based on the average data available across all other days
            caloriesum += (len(incomplete_days)
                           * (caloriesum
                              / (len(self.date_range) - len(incomplete_days))))
        self.caloriedatacoverage = ((len(self.date_range)
                                    - len(incomplete_days))
                                    / len(self.date_range))
        return caloriesum

    def weightchange_rate(self) -> float:
        """Returns the rate of observed weight change for the time period
        defined by the Mfp_range object, based on the data initially provided
        by the user."""
        weightdata = self.weight_data
        date_range = getdaterange(self.start_date, self.end_date + timedelta(1)
                                  )
        day_list = []
        day_count = 0
        weight_list = []
        days_nodata = 0
        for day in date_range:
            weight_reading = weightdata[day]
            day_count += 1
            if weight_reading is None:
                days_nodata += 1
                continue
            day_list.append(day_count)
            weight_list.append(weightdata[day])
        self.weightdatacoverage = (day_count - days_nodata) / day_count
        rate_data = np.array([day_list, weight_list])
        cov_matrix = np.cov(rate_data)
        slope = cov_matrix[0, 1]/cov_matrix[0, 0]
        return slope

    def get_deficit_surplus(self) -> float:
        """Returns the average daily caloric surplus (positive value) or
        deficit (negative value) for the date range defined by the Mfp_range
        object."""
        if self.ismetric:
            deficit_surplus = self.weightchange_rate() * 7700
        else:
            deficit_surplus = self.weightchange_rate() * 3492.66125192891
        return deficit_surplus

    def get_goalcalories(self, goal_monthly_change: float = 0) -> float:
        """Returns an individualised estimation of the daily caloric intake
        required to achieve the monthly weight change rate specified. The
        default weight change rate of 0 returns an individualised estimation
        of Total Daily Energy Expenditure (TDEE) the date range defined by the
        Mfp_range object."""
        avg_daily_intake = self.calories() / len(self.date_range)
        maintenance = avg_daily_intake - self.get_deficit_surplus()
        if self.ismetric:
            goalcalories = maintenance + goal_monthly_change * 7700 / 30
        else:
            goalcalories = (maintenance + goal_monthly_change
                            * 3492.66125192891 / 30)
        return goalcalories


def main():
    # Gather user input and assign input to variables that will be used to
    # instantiate a Mfp_range object
    username_prompt = "Please enter your MyFitnessPal username:"
    root = tk.Tk()
    root.withdraw()
    username = tkinter.simpledialog.askstring("Username",
                                              username_prompt,
                                              parent=root)
    root.destroy()
    password_prompt = "Please enter your MyFitnessPal password:"
    root = tk.Tk()
    root.withdraw()
    password = tkinter.simpledialog.askstring("Password",
                                              password_prompt,
                                              show="*",
                                              parent=root)
    root.destroy()
    client = myfitnesspal.Client(username, password)
    del username
    del password
    unit_prompt_title = "Measurement units"
    unit_prompt_body = ("Supported weight units are kilos/kg and"
                        " pounds/lbs. Is your data in kilos/kg? Select 'Yes' "
                        "for kilos/kg and 'No' for pounds/lbs.")
    root = tk.Tk()
    root.withdraw()
    ismetric = tkinter.messagebox.askyesno(unit_prompt_title,
                                           unit_prompt_body,
                                           parent=root)
    root.destroy()
    goal_title = "What is your weight change goal?"
    goal_body = ("How much weight would you like to gain/lose in a month?\nUse"
                 " a negative number if you want to lose weight or\na positive"
                 " number if you want to gain weight.\nUse 0 if you would like"
                 " to calculate your maintenance calories (TDEE).")
    root = tk.Tk()
    root.withdraw()
    user_goal = tkinter.simpledialog.askfloat(goal_title, goal_body,
                                              parent=root)
    root.destroy()
    weight_data = get_weightdata()
    # Instantiate a Mfp_range object based on the input the user provided. The
    # date range is defined by the date range provided by the user in their
    # weight record file.
    mfp_range = Mfp_range(min(weight_data.keys()),
                          max(weight_data.keys()),
                          client,
                          weight_data,
                          ismetric)
    # Calculate return values that the user will be interested in
    deficit_surplus = mfp_range.get_deficit_surplus()
    weekly_weight = mfp_range.weightchange_rate() * 7
    goal_cals = mfp_range.get_goalcalories(goal_monthly_change=user_goal)
    maint_cals = mfp_range.get_goalcalories(goal_monthly_change=0)
    # Format output to be returned to user
    if mfp_range.ismetric:
        unit = 'kg'
    else:
        unit = 'lbs'
    if deficit_surplus < 0:
        msg1 = (f"Your average daily deficit was {int(abs(deficit_surplus))}"
                " kcal.\n")
        msg2 = ("Your average weekly rate of weight loss was"
                f" {weekly_weight:.2f} {unit}.\n")
    else:
        msg1 = (f"Your average daily surplus was {int(abs(deficit_surplus))}"
                " kcal.\n")
        msg2 = ("Your average weekly rate of weight gain was"
                f" {weekly_weight:.2f} {unit}.\n")
    if goal_cals < -0.0000000000000001:
        msg3 = (f"Your maintenance intake is {int(maint_cals)} kcal per day."
                f"To lose {user_goal:.2f} {unit} per month, you would have to "
                f"eat an average of {int(goal_cals)} kcal per day.\n")
    elif goal_cals <= 0.0000000000000001:
        msg3 = f"Your maintenance intake is {int(maint_cals)} kcal per day.\n"
    else:
        msg3 = (f"Your maintenance intake is {int(maint_cals)} kcal per day. "
                f"To gain {user_goal:.2f} {unit} per month, you would have to "
                f"eat an average of {int(goal_cals)} kcal per day.\n")
    if mfp_range.isblankestimate:
        msg4 = (f"{(1 - mfp_range.caloriedatacoverage) * 100:.2f}% of days in "
                "the selected date range did not contain any food diary data "
                "in MyFitnessPal. The intake for these days was estimated "
                "based on the data for all other days.\n")
    else:
        msg4 = ""
    if mfp_range.weightdatacoverage < 0.6:
        msg5 = ("Weight readings were only available for "
                f"{mfp_range.weightdatacoverage * 100:.2f}% of days in the "
                "selected date range. This may decrease the accuracy of the "
                "estimations provided.")
    else:
        msg5 = ""
    concat_message = (msg1 + msg2 + msg3 + msg4 + msg5)
    print(concat_message)
    output_title = ("Calculation results for "
                    f"{mfp_range.start_date.strftime('%d %b %Y')} to "
                    f"{mfp_range.end_date.strftime('%d %b %Y')}")
    root_out = tk.Tk()
    root_out.withdraw()
    tkinter.messagebox.showinfo(output_title, concat_message,
                                parent=root_out)
    root_out.destroy()


if __name__ == "__main__":
    main()
