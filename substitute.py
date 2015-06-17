import tgl
from telex.DatabaseMixin import DatabaseMixin, DbType
from telex.utils.decorators import pm_only
from functools import partial
from telex import plugin
from urllib.parse import quote
import re


class SubstitutePlugin(plugin.TelexPlugin, DatabaseMixin):
    """
    Substitution plugin for Telex bot.
    """
    HISTORY_QUERY_SIZE = 1000

    patterns = {
        "^:(-\d*){0,1}s\/(.+)\/(.*)$": "substitute_message"
    }

    usage = [
        ":s/pattern/string: substitute pattern for string in the last message",
        ":-1s/pattern/string: substitute pattern for string in the second to last message"
    ]


    schema = {
        'msg_id': DbType.Integer,
        'timestamp': DbType.DateTime,
        'uid': DbType.Integer,
        'chat_id': DbType.Integer,
        'username': DbType.String,
        'name': DbType.String,
        'message': DbType.String,
    }
    primary_key = 'msg_id'

    def __init__(self):
        super().__init__()
        DatabaseMixin.__init__(self)

    def pre_process(self, msg):
        if not hasattr(msg, 'text'):
            return

        if hasattr(msg.src, 'username'):
            username = msg.src.username
        else:
            username = ""

        if msg.src.last_name:
            name = msg.src.first_name + ' ' + msg.src.last_name
        else:
            name = msg.src.first_name

        self.insert(msg_id=msg.id, timestamp=msg.date,
                    uid=msg.src.id, username=username,
                    name=name,
                    chat_id=msg.dest.id, message=msg.text)

    @pm_only
    def substitute_message(self, msg, matches):
        chat_id = msg.dest.id
        offset = 1
        if matches.group(1):
            offset =  int(matches.group(1)) * -1
        pattern = re.compile(matches.group(2))
        string = matches.group(3)

        query = """SELECT * FROM {0} WHERE chat_id == {1}
                   ORDER BY timestamp DESC LIMIT 1 OFFSET {2} COLLATE NOCASE""".format(self.table_name, chat_id, offset)
        self.query_and_sub(query, pattern, string, msg)

    def query_and_sub(self, query, pattern, string, msg):
        results = self.query(query)

        new_message = pattern.sub(string, results[0]["message"])

        peer = self.bot.get_peer_to_send(msg)
        txt = "{} FTFY".format(new_message)
        peer.send_msg(txt, reply=results[0]["msg_id"], preview=False)

