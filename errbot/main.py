from os import path, makedirs
import logging
import sys

log = logging.getLogger(__name__)


def setup_bot(bot_class, logger, config, restore = None):
    # from here the environment is supposed to be set (daemon / non daemon,
    # config.py in the python path )

    from .utils import PLUGINS_SUBDIR
    from .errBot import bot_config_defaults

    bot_config_defaults(config)

    if config.BOT_LOG_FILE:
        hdlr = logging.FileHandler(config.BOT_LOG_FILE)
        hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(hdlr)

    if config.BOT_LOG_SENTRY:
        try:
            from raven.handlers.logging import SentryHandler
        except ImportError:
            log.exception(
                "You have BOT_LOG_SENTRY enabled, but I couldn't import modules "
                "needed for Sentry integration. Did you install raven? "
                "(See http://raven.readthedocs.org/en/latest/install/index.html "
                "for installation instructions)"
            )
            exit(-1)

        sentryhandler = SentryHandler(config.SENTRY_DSN, level=config.SENTRY_LOGLEVEL)
        logger.addHandler(sentryhandler)

    logger.setLevel(config.BOT_LOG_LEVEL)

    # make the plugins subdir to store the plugin shelves
    d = path.join(config.BOT_DATA_DIR, PLUGINS_SUBDIR)
    if not path.exists(d):
        makedirs(d, mode=0o755)
    try:
        bot = bot_class(config)
    except Exception:
        log.exception("Unable to configure the backend, please check if your config.py is correct.")
        exit(-1)

    # restore the bot from the restore script
    if restore:
        # Prepare the context for the restore script
        bot = holder.bot  # gives the bot to the script
        if 'repos' in bot:
            log.fatal('You cannot restore onto a non empty bot.')
        from errbot.plugin_manager import get_plugin_by_name  # noqa
        log.info('**** RESTORING the bot from %s' % restore)
        with open(restore) as f:
            exec(f.read())
        bot.close_storage()
        print('Restore complete restore the bot normally')
        sys.exit(0)

    errors = holder.bot.update_dynamic_plugins()
    if errors:
        log.error('Some plugins failed to load:\n' + '\n'.join(errors))
    return bot


def main(bot_class, logger, config, restore = None):
    bot = setup_bot(bot_class, logger, config, restore)
    log.debug('serve from %s' % bot)
    bot.serve_forever()
