
import os
import yaml
import ga_core
import backend.helpers as helpers
# print("Working dir1: ", os.getcwd()) # DEBUGONLY

def summarise_data(df, args):
    agg_functions_from_raw = {
        'n_jobs': ('UserX', 'count'),
        'first_job_period': ('SubmitDatetimeX', 'min'),
        'last_job_period': ('SubmitDatetimeX', 'max'),
        'energy': ('energy', 'sum'),
        'energy_CPUs': ('energy_CPUs', 'sum'),
        'energy_GPUs': ('energy_GPUs', 'sum'),
        'energy_memory': ('energy_memory', 'sum'),
        'carbonFootprint': ('carbonFootprint', 'sum'),
        'carbonFootprint_memoryNeededOnly': ('carbonFootprint_memoryNeededOnly', 'sum'),
        'carbonFootprint_failedJobs': ('carbonFootprint_failedJobs', 'sum'),
        'cpuTime': ('TotalCPUtime2useX', 'sum'),
        'gpuTime': ('TotalGPUtime2useX', 'sum'),
        'wallclockTime': ('WallclockTimeX', 'sum'),
        'CPUhoursCharged': ('CPUhoursChargedX', 'sum'),
        'GPUhoursCharged': ('GPUhoursChargedX', 'sum'),
        'memoryRequested': ('ReqMemX', 'sum'),
        'memoryOverallocationFactor': ('memOverallocationFactorX', 'mean'),
        'n_success': ('StateX', 'sum'),
        'treeMonths': ('treeMonths', 'sum'),
        'treeMonths_memoryNeededOnly': ('treeMonths_memoryNeededOnly', 'sum'),
        'treeMonths_failedJobs': ('treeMonths_failedJobs', 'sum'),
        'driving': ('driving', 'sum'),
        'flying_NY_SF': ('flying_NY_SF', 'sum'),
        'flying_PAR_LON': ('flying_PAR_LON', 'sum'),
        'flying_NYC_MEL': ('flying_NYC_MEL', 'sum'),
        'cost': ('cost', 'sum'),
        'cost_failedJobs': ('cost_failedJobs', 'sum'),
        'cost_memoryNeededOnly': ('cost_memoryNeededOnly', 'sum'),
    }

    # This is to aggregate already aggregated dataset (so names are a bit different)
    agg_functions_further = agg_functions_from_raw.copy()
    agg_functions_further['n_jobs'] = ('n_jobs', 'sum')
    agg_functions_further['first_job_period'] = ('first_job_period', 'min')
    agg_functions_further['last_job_period'] = ('last_job_period', 'max')
    agg_functions_further['cpuTime'] = ('cpuTime', 'sum')
    agg_functions_further['gpuTime'] = ('gpuTime', 'sum')
    agg_functions_further['wallclockTime'] = ('wallclockTime', 'sum')
    agg_functions_further['CPUhoursCharged'] = ('CPUhoursCharged', 'sum')
    agg_functions_further['GPUhoursCharged'] = ('GPUhoursCharged', 'sum')
    agg_functions_further['memoryRequested'] = ('memoryRequested', 'sum')
    agg_functions_further['memoryOverallocationFactor'] = ('memoryOverallocationFactor', 'mean') # NB: not strictly correct to do a mean of mean, but ok
    agg_functions_further['n_success'] = ('n_success', 'sum')

    def agg_jobs(data, agg_names=None):
        """

        :param data:
        :param agg_names: if None, then the whole dataset is aggregated
        :return:
        """
        agg_names2 = agg_names if agg_names else lambda _:True
        if 'UserX' in data.columns:
            timeseries = data.groupby(agg_names2).agg(**agg_functions_from_raw)
        else:
            timeseries = data.groupby(agg_names2).agg(**agg_functions_further)

        timeseries.reset_index(inplace=True, drop=(agg_names is None))
        timeseries['success_rate'] = timeseries.n_success / timeseries.n_jobs
        timeseries['failure_rate'] = 1 - timeseries.success_rate
        timeseries['share_carbonFootprint'] = timeseries.carbonFootprint / timeseries.carbonFootprint.sum()

        return timeseries

    df['SubmitDate'] = df.SubmitDatetimeX.dt.date  # TODO do it with real start time rather than submit day

    df_userdaily = agg_jobs(df, ['SubmitDate'])
    df_overallStats = agg_jobs(df_userdaily)
    dict_overallStats = df_overallStats.iloc[0, :].to_dict()
    userID = df.UserX.iloc[0]

    output = {
        "userDaily": df_userdaily,
        'userActivity': {userID: dict_overallStats},
        "user": userID
    }

    # Some job-level statistics to plot distributions
    memoryOverallocationFactors = df.groupby('UserX')['memOverallocationFactorX'].apply(list).to_dict()
    memoryOverallocationFactors['overall'] = df.memOverallocationFactorX.to_numpy()
    output['memoryOverallocationFactors'] = memoryOverallocationFactors

    return output

def prepare_ga_config(args):
    """
    Prepare the configuration for the GA core, based on the command line arguments.
    :param args: [argparse.Namespace] the command line arguments
    :return: [dict] the configuration for the GA core
    """
    ga_config = {
        "useCustomLogs": args.useCustomLogs,
        "startDay": args.startDay,
        "endDay": args.endDay,
        }
    
    optional_args = ["filterWD", "filterJobIDs", "filterAccount", "userCWD", "customSuccessStates"] # Need to be implemented in a better manner, perhaps by importing a model from ga_core
    for arg in optional_args:
        if getattr(args, arg):
            ga_config[arg] = getattr(args, arg)

    return ga_config
    
def main_backend(args):
    '''

    :param args:
    :return:
    '''
    ga_config = prepare_ga_config(args)
    ### Load cluster specific info
    with open(os.path.join(args.path_infrastucture_info, 'cluster_info.yaml'), "r") as stream:
        try:
            cluster_info = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    ### Load fixed parameters
    with open("data/fixed_parameters.yaml", "r") as stream:
        try:
            fParams = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    dataprocessor = ga_core.HPCDataProcessor(ga_config, cluster_info, fParams, all_users_access = False)
    df = dataprocessor.extract_data()

    helpers.check_empty_results(df, args) # Check if any jobs have been run on the period, and stop the script if not.

    df2 = dataprocessor.enrich_data(df)
    summary_stats = summarise_data(df2, args=args)

    return summary_stats

if __name__ == "__main__":

    #### This is used for testing only ####

    from collections import namedtuple
    argStruct = namedtuple('argStruct',
                           'startDay endDay use_mock_agg_data useCustomLogs customSuccessStates filterWD filterJobIDs filterAccount reportBug reportBugHere path_infrastucture_info')
    args = argStruct(
        startDay='2022-01-01',
        endDay='2023-06-30',
        useCustomLogs=None,
        use_mock_agg_data=True,
        customSuccessStates='',
        filterWD=None,
        filterJobIDs='all',
        filterAccount=None,
        reportBug=False,
        reportBugHere=False,
        path_infrastucture_info="clustersData/CSD3",
    )

    main_backend(args)



