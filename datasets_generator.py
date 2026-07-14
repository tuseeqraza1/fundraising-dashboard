"""Synthetic data generator for a German fundraising dashboard (Power BI).

Generates four related tables with German donors, campaigns and EUR amounts,
spanning 2021-01-01 to 2026-12-31. All data is synthetic.

Usage:   python generate_datasets.py
Outputs: donors.csv, campaigns.csv, donations.csv, calendar.csv
"""

import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

# --- Configuration ---
NUM_DONORS = 16800
START_DATE = datetime(2021, 1, 1)
END_DATE = datetime(2026, 12, 31)
AS_OF_DATE = datetime(2026, 7, 1)  # reference date for campaign/donor status

# --- German reference data ---
FIRST_NAMES = [
    'Alexander', 'Andreas', 'Anna', 'Birgit', 'Christian', 'Claudia', 'Daniel',
    'Elias', 'Emma', 'Felix', 'Finn', 'Frank', 'Hannah', 'Heike', 'Jan',
    'Johanna', 'Jonas', 'Julia', 'Jürgen', 'Katharina', 'Klaus', 'Laura',
    'Lena', 'Leon', 'Lukas', 'Marie', 'Markus', 'Martina', 'Max', 'Mia',
    'Michael', 'Monika', 'Nicole', 'Niklas', 'Paul', 'Petra', 'Sabine',
    'Sandra', 'Sofia', 'Stefan', 'Susanne', 'Thomas', 'Ursula', 'Wolfgang',
]
LAST_NAMES = [
    'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner',
    'Becker', 'Schulz', 'Hoffmann', 'Schäfer', 'Koch', 'Bauer', 'Richter',
    'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann', 'Braun',
    'Krüger', 'Hofmann', 'Hartmann', 'Lange', 'Schmitt', 'Werner', 'Krause',
    'Meier', 'Lehmann', 'Huber', 'Mayer', 'Herrmann', 'König', 'Walter',
    'Peters', 'Möller', 'Weiß', 'Jung', 'Vogel',
]
STREETS = [
    'Hauptstraße', 'Bahnhofstraße', 'Gartenstraße', 'Schulstraße', 'Dorfstraße',
    'Bergstraße', 'Lindenstraße', 'Kirchgasse', 'Goethestraße', 'Schillerstraße',
    'Mozartstraße', 'Ringstraße', 'Am Markt', 'Waldweg', 'Rosenweg',
    'Birkenweg', 'Feldstraße', 'Wiesenweg', 'Beethovenstraße', 'Marktplatz',
]
# City -> (weight, PLZ range) for realistic 5-digit German postal codes.
CITIES = {
    'Berlin': (18, (10115, 14199)), 'Hamburg': (10, (20095, 22769)),
    'München': (8, (80331, 81929)), 'Köln': (6, (50667, 51149)),
    'Frankfurt am Main': (5, (60306, 60599)), 'Stuttgart': (4, (70173, 70629)),
    'Düsseldorf': (4, (40210, 40629)), 'Leipzig': (4, (4103, 4357)),
    'Dortmund': (3, (44135, 44388)), 'Essen': (3, (45127, 45359)),
    'Bremen': (3, (28195, 28779)), 'Dresden': (3, (1067, 1326)),
    'Hannover': (3, (30159, 30659)), 'Nürnberg': (2, (90402, 90491)),
    'Bonn': (2, (53111, 53229)), 'Mainz': (2, (55116, 55131)),
}
CITY_NAMES = list(CITIES)
CITY_WEIGHTS = [CITIES[c][0] for c in CITY_NAMES]
EMAIL_DOMAINS = ['gmx.de', 'web.de', 't-online.de', 'gmail.com', 'outlook.de']
MOBILE_PREFIXES = ['151', '152', '157', '160', '170', '171', '172', '175', '176', '179']
UMLAUT_MAP = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'})

# Monthly donation weights: year-round giving with a mild Nov/Dec lift and slight summer dip.
MONTH_WEIGHTS = np.array([1.0, 0.95, 1.0, 1.0, 0.95, 0.9, 0.85, 0.9, 1.0, 1.05, 1.25, 1.4])
MONTH_WEIGHTS = MONTH_WEIGHTS / MONTH_WEIGHTS.sum()


def slugify(name):
    """Lowercase name with umlauts transliterated, for email addresses."""
    return name.lower().translate(UMLAUT_MAP)


def german_phone():
    return f"+49 {random.choice(MOBILE_PREFIXES)} {random.randint(1000000, 9999999)}"


def seasonal_date(start, end):
    """Random date in [start, end], weighted toward the year-end giving season."""
    for _ in range(30):
        year = random.randint(start.year, end.year)
        month = int(np.random.choice(np.arange(1, 13), p=MONTH_WEIGHTS))
        d = datetime(year, month, random.randint(1, 28))
        if start <= d <= end:
            return d
    return start + timedelta(days=random.randint(0, (end - start).days))


def easter_sunday(year):
    """Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month = (h + l - 7 * m + 90) // 25
    day = (h + l - 7 * m + 33 * month + 19) % 32
    return date(year, month, day)


def german_holidays(years):
    """Nationwide German public holidays; uses the holidays library if available."""
    try:
        import holidays
        return set(holidays.Germany(years=years).keys())
    except ImportError:
        result = set()
        for y in years:
            easter = easter_sunday(y)
            result.update({
                date(y, 1, 1),                        # Neujahr
                easter - timedelta(days=2),           # Karfreitag
                easter + timedelta(days=1),           # Ostermontag
                date(y, 5, 1),                        # Tag der Arbeit
                easter + timedelta(days=39),          # Christi Himmelfahrt
                easter + timedelta(days=50),          # Pfingstmontag
                date(y, 10, 3),                       # Tag der Deutschen Einheit
                date(y, 12, 25),                      # 1. Weihnachtstag
                date(y, 12, 26),                      # 2. Weihnachtstag
            })
        return result


# --- donors ---
print("Generating donors...")
donors = []
for i in range(NUM_DONORS):
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Email: 10% missing or malformed (data-quality exercise)
    if random.random() < 0.10:
        email = "" if random.random() < 0.5 else f"{slugify(first_name)}.{slugify(last_name)}"
    else:
        email = f"{slugify(first_name)}.{slugify(last_name)}@{random.choice(EMAIL_DOMAINS)}"

    phone = "" if random.random() < 0.15 else german_phone()

    city = random.choices(CITY_NAMES, weights=CITY_WEIGHTS)[0]
    plz_lo, plz_hi = CITIES[city][1]
    # Postcode: 5% invalid (4 digits only)
    postcode = str(random.randint(100, 9999)) if random.random() < 0.05 else f"{random.randint(plz_lo, plz_hi):05d}"

    acquisition_year = int(np.random.choice(range(2021, 2027), p=[0.10, 0.13, 0.16, 0.19, 0.21, 0.21]))
    year_start = datetime(acquisition_year, 1, 1)
    year_end = min(datetime(acquisition_year, 12, 31), END_DATE)
    acquisition_date = year_start + timedelta(days=random.randint(0, (year_end - year_start).days))

    donors.append({
        'donor_id': 1000 + i,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'address_line1': f"{random.choice(STREETS)} {random.randint(1, 160)}",
        'city': city,
        'postcode': postcode,
        'acquisition_date': acquisition_date,
        'acquisition_channel': np.random.choice(
            ['Online', 'Direct Mail', 'Event', 'Telemarketing', 'Legacy'],
            p=[0.35, 0.25, 0.20, 0.15, 0.05]),
        'donor_status': 'Active',  # updated after donations are generated
        'communication_preference': np.random.choice(
            ['Email', 'Post', 'Phone', 'None'], p=[0.50, 0.30, 0.15, 0.05]),
    })

donors_df = pd.DataFrame(donors)

# --- campaigns ---
print("Generating campaigns...")
EMERGENCIES = {
    2021: 'Nothilfe Hochwasser Ahrtal', 2022: 'Nothilfe Ukraine',
    2023: 'Nothilfe Erdbeben Türkei-Syrien', 2024: 'Nothilfe Hochwasser Süddeutschland',
    2025: 'Nothilfe Dürre Ostafrika', 2026: 'Nothilfe Erdbeben Südosteuropa',
}
THEMES = ['Sauberes Wasser', 'Bildungschancen', 'Gesundheit für alle', 'Klimaschutz vor Ort']
EVENTS = ['Spendenlauf Berlin', 'Benefizkonzert Köln', 'Charity-Gala München',
          'Spendenlauf Hamburg', 'Benefizkonzert Leipzig', 'Charity-Gala Frankfurt']

campaigns = []
campaign_id = 100
for year in range(2021, 2027):
    year_specs = [
        # (name, type, start, duration_days, target range)
        (f'Weihnachtsspende {year}', 'Weihnachtsaktion',
         datetime(year, 11, random.randint(5, 15)), 50, (60000, 120000)),
        (EMERGENCIES[year], 'Nothilfe',
         datetime(year, random.randint(2, 10), random.randint(1, 28)),
         random.randint(21, 45), (50000, 150000)),
        (f'{THEMES[year % 4]} {year}', 'Frühjahrskampagne',
         datetime(year, random.randint(4, 5), random.randint(1, 28)),
         random.randint(45, 75), (25000, 75000)),
        (f'{THEMES[(year + 2) % 4]} {year}', 'Herbstkampagne',
         datetime(year, 9, random.randint(1, 15)),
         random.randint(50, 75), (25000, 75000)),
        (f'Dauerspender-Aktion {year}', 'Dauerspender',
         datetime(year, 1, random.randint(2, 15)),
         random.randint(75, 105), (30000, 80000)),
        (f'Osteraktion {year}', 'Saisonaktion',
         datetime(year, 3, random.randint(15, 28)), random.randint(30, 45), (20000, 50000)),
        (f'Ferienhilfe {year}', 'Ferienhilfe',
         datetime(year, 6, random.randint(1, 28)), random.randint(45, 75), (20000, 60000)),
        (f'{EVENTS[year % 6]} {year}', 'Benefiz-Event',
         datetime(year, random.randint(5, 9), random.randint(1, 28)),
         random.randint(1, 3), (10000, 30000)),
    ]
    for name, ctype, start, duration, target_range in year_specs:
        end = min(start + timedelta(days=duration), END_DATE)
        if end < AS_OF_DATE:
            status = 'Completed'
        elif start > AS_OF_DATE:
            status = 'Planned'
        else:
            status = 'Active'
        campaigns.append({
            'campaign_id': campaign_id,
            'campaign_name': name,
            'campaign_type': ctype,
            'start_date': start,
            'end_date': end,
            'target_amount': random.randint(*target_range),
            'campaign_status': status,
        })
        campaign_id += 1

campaigns_df = pd.DataFrame(campaigns)

# --- donations ---
print("Generating donations...")
camp_ids = campaigns_df['campaign_id'].to_numpy()
camp_starts = campaigns_df['start_date'].to_list()
camp_ends = campaigns_df['end_date'].to_list()
# Bigger campaigns draw more gifts; sqrt damping keeps volume spread across the year
camp_weights = np.sqrt(campaigns_df['target_amount'].to_numpy().astype(float))

donations = []
donation_id = 10000
for donor in donors:
    segment = np.random.choice(
        ['Champion', 'Loyal', 'Occasional', 'One-time', 'Lapsed'],
        p=[0.08, 0.15, 0.35, 0.30, 0.12])
    if segment == 'Lapsed':
        continue

    # Typical German gift sizes in EUR (median ~25-45 EUR)
    avg_gift = np.random.lognormal(3.8, 0.9) if segment in ('Champion', 'Loyal') else np.random.lognormal(3.3, 0.7)
    frequency_per_year = {'Champion': random.randint(6, 12), 'Loyal': random.randint(3, 6),
                          'Occasional': random.randint(1, 3), 'One-time': 0}[segment]
    regular_giver = segment in ('Champion', 'Loyal') and random.random() < 0.45

    acq = donor['acquisition_date']
    years_active = (END_DATE - acq).days / 365.25
    num_gifts = 1 if segment == 'One-time' else max(1, int(frequency_per_year * years_active))

    # Campaigns eligible for this donor (started after acquisition)
    eligible = [j for j, s in enumerate(camp_starts) if s >= acq]
    eligible_weights = [camp_weights[j] for j in eligible]

    for gift_num in range(num_gifts):
        # ~20% of gifts stay unassigned (first gift at acquisition, few spontaneous ones)
        if gift_num == 0:
            donation_date, gift_campaign_id = acq, None
        elif eligible and random.random() < 0.98:
            j = random.choices(eligible, weights=eligible_weights)[0]
            window_days = (camp_ends[j] - camp_starts[j]).days
            donation_date = camp_starts[j] + timedelta(days=random.randint(0, window_days))
            gift_campaign_id = int(camp_ids[j])
        else:
            donation_date, gift_campaign_id = seasonal_date(acq, END_DATE), None

        amount = max(5.0, round(np.random.normal(avg_gift, avg_gift * 0.3), 2))
        if regular_giver and random.random() < 0.85:
            payment_method = 'SEPA-Lastschrift'
        else:
            payment_method = np.random.choice(
                ['SEPA-Lastschrift', 'Überweisung', 'PayPal', 'Kreditkarte'],
                p=[0.40, 0.28, 0.18, 0.14])
        donations.append({
            'donation_id': donation_id,
            'donor_id': donor['donor_id'],
            'donation_date': donation_date,
            'amount': amount,
            'campaign_id': gift_campaign_id,
            'payment_method': payment_method,
            'gift_type': 'Regular' if regular_giver and random.random() < 0.9 else 'One-off',
            'gift_aid_claimed': 'Yes' if random.random() < 0.55 else 'No',
        })
        donation_id += 1

donations_df = pd.DataFrame(donations)

# Donor status from giving recency: no gifts or >2 years silent -> Lapsed
last_gift = donations_df.groupby('donor_id')['donation_date'].max()
donors_df['last_gift'] = donors_df['donor_id'].map(last_gift)
days_since = (AS_OF_DATE - donors_df['last_gift']).dt.days
lapsed = donors_df['last_gift'].isna() | (days_since > 730)
deceased = ~lapsed & (np.random.random(len(donors_df)) < 0.01)
donors_df['donor_status'] = np.select([lapsed, deceased], ['Lapsed', 'Deceased'], default='Active')
donors_df = donors_df.drop(columns='last_gift')

# --- calendar ---
print("Generating calendar...")
holiday_dates = german_holidays(range(2021, 2027))
calendar_df = pd.DataFrame({'date': pd.date_range(START_DATE, END_DATE, freq='D')})
calendar_df['year'] = calendar_df['date'].dt.year
calendar_df['quarter'] = calendar_df['date'].dt.quarter
calendar_df['month_number'] = calendar_df['date'].dt.month
calendar_df['month_name'] = calendar_df['date'].dt.strftime('%B')
calendar_df['week_number'] = calendar_df['date'].dt.isocalendar().week.astype(int)
calendar_df['day_of_week'] = calendar_df['date'].dt.strftime('%A')
calendar_df['is_weekend'] = calendar_df['date'].dt.weekday >= 5
calendar_df['is_bank_holiday'] = calendar_df['date'].dt.date.isin(holiday_dates)
# German fiscal year matches the calendar year
calendar_df['financial_year'] = calendar_df['year']
calendar_df['financial_quarter'] = calendar_df['quarter']
calendar_df['financial_month'] = calendar_df['month_number']

# --- integrity checks and export ---
assert donations_df['donor_id'].isin(donors_df['donor_id']).all()
assert donations_df['campaign_id'].dropna().isin(campaigns_df['campaign_id']).all()
assert donations_df['donation_date'].between(START_DATE, END_DATE).all()
assert donors_df['acquisition_date'].between(START_DATE, END_DATE).all()

datasets = {
    'donors.csv': donors_df,
    'campaigns.csv': campaigns_df,
    'donations.csv': donations_df,
    'calendar.csv': calendar_df,
}
print("\nSummary:")
for filename, df in datasets.items():
    df.to_csv(filename, index=False, date_format='%Y-%m-%d', encoding='utf-8-sig')
    print(f"  {filename:15} {len(df):>8,} rows")
