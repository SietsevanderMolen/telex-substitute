import tgl
from telex.DatabaseMixin import DatabaseMixin, DbType
from telex.utils.decorators import group_only
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
        "^:(.*)s\/(.+)\/(.+)$": "substitute"
    }

    usage = [
        "s/pattern/string"
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

    def substitute(self, msg, matches):
        chat_id = msg.dest.id
        username = matches.group(1)
        pattern = re.compile(matches.group(2))
        string = matches.group(3)

        if username:  # sub for person
            query = """SELECT * FROM {0}
                       WHERE username == ? AND chat_id == {1}
                       ORDER BY timestamp DESC LIMIT 1 COLLATE NOCASE""".format(self.table_name, chat_id)
            results = self.query(query, parameters=(username,))
        else:  # sub general
            query = """SELECT * FROM {0} WHERE chat_id == {1}
                       ORDER BY timestamp DESC LIMIT 1 OFFSET 1 COLLATE NOCASE""".format(self.table_name, chat_id)
            results = self.query(query)

        new_message = pattern.sub(string, results[0]["message"])

        peer = self.bot.get_peer_to_send(msg)
        txt = "{}".format(new_message)
        peer.send_msg(txt, reply=results[0]["msg_id"], preview=False)
