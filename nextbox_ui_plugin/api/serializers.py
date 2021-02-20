from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from nextbox_ui_plugin.models import SavedTopology
from users.api.nested_serializers import NestedUserSerializer
import datetime
import json

class SavedTopologySerializer(serializers.ModelSerializer):

    def to_internal_value(self, data):
        validated = {
            'topology': json.loads(data.get('topology')),
            'user': self.context['request'].user,
            'timestamp': str(datetime.datetime.now())
        }
        return validated

    class Meta:
        model = SavedTopology
        fields = [
            "id", "topology", "user", "timestamp"
        ]
