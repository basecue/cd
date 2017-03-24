def configuration_with_option(configuration, configuration_option):
    return ':'.join(filter(bool, (configuration, configuration_option)))