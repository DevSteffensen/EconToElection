from scipy import stats
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
COUNTRIES=SCRIPT_DIR.joinpath('Countries').glob('*')


def getFocusedIdeologies(project_directory : Path) -> set:
    ideologies_path = project_directory.joinpath('data/ideologies.csv')
    with open(ideologies_path) as ideologies_file:
        focused_ideologies_set = set()
        line = ideologies_file.readline()
        while line != "":
            focused_ideologies_set.add(line.strip())
            line = ideologies_file.readline()

    return focused_ideologies_set


def getElections(country : Path, focused_ideologies : set) -> dict[int, float]:
    focused_performance = {}
    elections = country.glob('elections/*')
    for election in elections:
        election_name = int(election.name.split('/')[-1])
        percentage = 0
        with open(election.joinpath('elections.csv')) as election_file:
            # NOTE: gets rid of a header
            election_file.readline()
            line = election_file.readline()
            while line != "":
                line = line.strip().split(',')
                ideology = line[1]

                if ideology in focused_ideologies:
                    percentage += float(line[2])

                line = election_file.readline()

        focused_performance[election_name] = percentage

    return focused_performance


def getCountryTag(country : Path) -> str:
    return country.stem

# election years go from lowest to highest
def getMeanGDP(project_directory : Path, election_years : list, country_tag) -> dict[int, float]:
    COMMENT_HEIGHT = 4
    BASE_GAP = 4
    GDP_path = project_directory.joinpath('data/GDP.csv')
    with open(GDP_path) as GDP_file:
        for i in range(COMMENT_HEIGHT):
            GDP_file.readline()

        header = GDP_file.readline().replace("\"", "").strip().split(',')

        line = GDP_file.readline().strip().split("\",\"")
        while line != "":
            current_tag = line[1]
            if current_tag == country_tag:
                break
            line = GDP_file.readline().strip().split("\",\"")

        line[0] = line[0].replace("\"", "")
        line[-1] = line[-1].replace("\"", "")

        interval_GDP = {}
        last_election_year = election_years[0] - BASE_GAP
        year_index = 0

        # NOTE Problem with index acquisition, so we manually check indexes
        for field in header:
            if str(last_election_year) == field.replace("\"", ""):
                break
            year_index += 1

        for year in election_years:
            GDP_yearly_growth_sum = 0
            governance_years = year - last_election_year
            for i in range(governance_years):
                year_index += 1
                GDP_growth = float(line[year_index].replace("\"", ""))
                GDP_yearly_growth_sum += GDP_growth

            meanGDP = GDP_yearly_growth_sum / governance_years
            interval_GDP[year] = meanGDP
            last_election_year = year

        return interval_GDP



def findCorrelation(ideological_performance : dict[int, float], economic_performance : dict[int, float]):
    economy = []
    performances = []
    for year in economic_performance:
        economy.append(economic_performance[year])
        performances.append(ideological_performance[year])

    slope, intercept, r_value, p_value, std_err = stats.linregress(economy, performances)

    print("Slope:", slope)
    print("R squared:", r_value ** 2)
    print("P-value:", p_value)


watched_ideologies = getFocusedIdeologies(SCRIPT_DIR)


for c in COUNTRIES:
    ideologies = getElections(c, watched_ideologies)

    years = list(ideologies.keys())
    years.sort()

    growth = getMeanGDP(SCRIPT_DIR, years, getCountryTag(c))

    findCorrelation(ideologies, growth)

