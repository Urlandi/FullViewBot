# -*- coding: utf-8 -*-

keyboard_buttons_name = {"help_name": "Help",
                         "settings_name": "Settings",
                         "last_status_name": "Last status", }

main_keyboard_template = ((keyboard_buttons_name["help_name"], keyboard_buttons_name["settings_name"],),
                          (keyboard_buttons_name["last_status_name"],))


switch_buttonv4_name = "{:s}IPv4 table status{:s}"
switch_buttonv6_name = "{:s}IPv6 table status{:s}"


selected_arrow_left = "[✓] "
selected_arrow_right = ""

empty_arrow_left = "[    ] "
empty_arrow_right = ""

echo_msg = "Unfortunately, I didn't understand what do you mean. \
If you have any questions or notes, \
please contact my author by <a href=\"https://t.me/UrgentPirate\">Telegram</a> \
or by <a href=\"https://github.com/Urlandi/FullViewBot/issues\">GitHub</a>.\n\n\
Also the /help command shows some helpful information about me."


settings_msg = "You may choose about which BGP full view - IPv4, or IPv6, or both you'll receive."

help_msg = "Hello, I'm a BGP FullView Telegram bot. I calculate some statistic about IP prefixes and ASes from the \
<a href=\"http://data.ris.ripe.net/rrc00/\">rrc00/latest-bview.gz</a> \
raw data file which is managed by the \
<a href=\"https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris\
/routing-information-service-ris\">RIPE NCC RIS project</a> and contains a whole Internet route table dump.\n\n\
Please go to the /settings menu, where you can setup which BGP table statistic v4 or v6 you would like to see. \
The /start command subscribes you to all updates and the /stop unsubscribes and mutes.\n\n\
Updates are every 8 hours at 6, 14, and 22 o'clock MSK timezone. \
The command /status sends the last posted status to the stream.\n\n\
Was inspired by <a href=\"https://twitter.com/mellowdrifter\">Darren O'Connor</a> and his Twitter bots. \
My author @UrgentPirate is open for questions and proposals. \
My code is on <a href=\"https://github.com/Urlandi/FullViewBot/issues\">GitHub.</a>"

stop_msg = "Unsubscribed. Try the /start or the /settings for return."

start_msg = "Great, now you have been subscribed for all updates. \
Please read the /help page or make your own customization directly via the /settings, if it needed."

subscriptions_empty_msg = "Oops, you haven't any subscriptions now. Go to the /settings menu to fix this. \
If you don't know what can you do, please read the /help page."

bgp4_status_msg = "There are <b>{:d}</b> prefixes from {:d} ASes in the BGPv4 full view{:s} " \
                  "\nThe most encounter /{:s} has {:.1f}% of the total. " \
                  "{:.1f}% ASes announce IPv4 prefixes only, and {:.1f}% are 32-bit ASn." \
                  "\n--- <i><a href=\"https://www.ris.ripe.net/peerlist/all.shtml\">rrc00</a> at {:s}</i>"
bgp6_status_msg = "There are <b>{:d}</b> prefixes from {:d} ASes in the BGPv6 full view{:s} " \
                  "\nThe most encounter /{:s} has {:.1f}% of the total. " \
                  "{:.1f}% ASes announce IPv6 prefixes only, and {:.1f}% are 32-bit ASn." \
                  "\n--- <i><a href=\"https://www.ris.ripe.net/peerlist/all.shtml\">rrc00</a> at {:s}</i>"
bgp_changed_msg = ", {:+d} prefixes since last dump, {:+d} since last week."

bgp4_prefix_length_chart_title = 'Top of IPv4 prefixes'
bgp6_prefix_length_chart_title = 'Top of IPv6 prefixes'

bgp4_prefix_trend_chart_title = '{:s} BGPv4 full view changes'
bgp6_prefix_trend_chart_title = '{:s} BGPv6 full view changes'

bgp4_ases_trend_chart_title = '{:s} BGPv4 ASn count changes'
bgp6_ases_trend_chart_title = '{:s} BGPv6 ASn count changes'
