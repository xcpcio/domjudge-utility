class DumpConfig:
    @staticmethod
    def get_config_with_default_value(config_dict, key, default_value):
        if key in config_dict.keys():
            return config_dict[key]

        return default_value

    class ExportedData:
        def __init__(self, exported_data_dict):
            self.domjudge_api = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'domjudge_api', True)

            # Since the export of event-feed may be a bit slow
            # we do not export by default
            self.event_feed = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'event_feed', False)

            self.runs = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'runs', False)

            self.source_code = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'submissions', False)

            self.images = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'images', False)

            self.ghost_dat_data = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'ghost_dat_data', False)

            self.resolver_data = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'resolver_data', False)

            self.scoreboard_excel_data = DumpConfig.get_config_with_default_value(
                exported_data_dict, 'scoreboard_excel_data', False)

    def __init__(self, config_dict={}):
        self.base_file_path = self.get_config_with_default_value(
            config_dict, 'base_file_path', '')

        self.base_url = self.get_config_with_default_value(
            config_dict, 'base_url', '')

        self.userpwd = self.get_config_with_default_value(
            config_dict, 'userpwd', '')

        self.cid = self.get_config_with_default_value(config_dict, 'cid', 0)

        self.api_version = self.get_config_with_default_value(
            config_dict, 'api_version', 'v4')

        self.saved_dir = self.get_config_with_default_value(
            config_dict, 'saved_dir', './output')

        self.score_in_seconds = self.get_config_with_default_value(
            config_dict, 'score_in_seconds', False)

        # Since Ghost Dat Data with Chinese team names may be garbled
        # when imported into Codeforces,
        # We found that if some dummy Russian teams are added, it may works.
        # This configuration field is only for exporting ghost dat data
        # defaults to `false`
        self.add_dummy_russian_team = self.get_config_with_default_value(
            config_dict, 'add_dummy_russian_team', False)

        # Since there are too many requests to send when downloading source code,
        # we use `grequests` to send in parallel,
        # this configuration field can set the number of parallel sending
        # defaults to `100`
        self.grequests_parallels_nums = self.get_config_with_default_value(
            config_dict, 'grequests_parallels_nums', 100)

        self.exported_data = DumpConfig.ExportedData(
            config_dict['exported_data'] if 'exported_data' in config_dict.keys() else {})
