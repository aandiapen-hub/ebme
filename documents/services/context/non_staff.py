from urllib.parse import urlencode
from .context import BaseDocumentContextBuilder
from .asset_data import get_fully_matched_asset, get_partially_matched_asset

from .context_action import(
    MatchedGroup,
)

class NonStaffContext(
    BaseDocumentContextBuilder
):

    def template_name(self):
        return 'documents/document_processor/asset_data.html'

    def get_extra_context(self):

        temp_group = self.get_temp_group_id()

        exact_match_group = MatchedGroup(
            title='Exact Matches',
            confidence='Full',
            items=[],
            color='success')
        exact_match_group.items += get_fully_matched_asset(
            self.resolved_data,  self.get_temp_group_id()
        )


        partial_matches = MatchedGroup(
            title='Partial Matches (matched on serial number only)',
            confidence='partial',
            items=[],
            color='secondary')

        partial_matches.items += get_partially_matched_asset(
                self.resolved_data,  temp_group
        )

        return {
            'groups': [
                exact_match_group,
                partial_matches,
            ]}
