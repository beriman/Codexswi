from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.services.profile import InMemoryProfileGateway


class FakeSupabaseProfileGateway(InMemoryProfileGateway):
    """Test double exposing follow write operations for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.follow_writes: List[tuple[str, str]] = []
        self.unfollow_writes: List[tuple[str, str]] = []
        self.profile_updates: List[Dict[str, Dict[str, Any]]] = []

    async def create_follow(self, *, follower_id: str, following_id: str) -> None:  # type: ignore[override]
        await super().create_follow(follower_id=follower_id, following_id=following_id)
        self.follow_writes.append((follower_id, following_id))

    async def delete_follow(self, *, follower_id: str, following_id: str) -> None:  # type: ignore[override]
        await super().delete_follow(follower_id=follower_id, following_id=following_id)
        self.unfollow_writes.append((follower_id, following_id))

    async def update_profile(  # type: ignore[override]
        self, profile_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        updated = await super().update_profile(profile_id, payload)
        self.profile_updates.append({profile_id: payload})
        return updated

    async def reset_relationships(self) -> None:  # type: ignore[override]
        await super().reset_relationships()
        self.follow_writes.clear()
        self.unfollow_writes.clear()
        self.profile_updates.clear()


@pytest.fixture
def fake_profile_gateway() -> FakeSupabaseProfileGateway:
    return FakeSupabaseProfileGateway()


class FakeSupabaseResult:
    """Mock result from Supabase query."""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data


class FakeSupabaseTable:
    """Mock Supabase table interface."""
    
    def __init__(self, name: str, storage: Dict[str, List[Dict[str, Any]]]):
        self.name = name
        self.storage = storage
        self._filters: List[tuple[str, str, Any]] = []
        self._select_fields = '*'
        self._order_field: Optional[tuple[str, bool]] = None
    
    def select(self, fields: str = '*'):
        """Mock select operation."""
        self._select_fields = fields
        return self
    
    def eq(self, field: str, value: Any):
        """Mock equality filter."""
        self._filters.append(('eq', field, value))
        return self
    
    def in_(self, field: str, values: List[Any]):
        """Mock IN filter."""
        self._filters.append(('in', field, values))
        return self
    
    def order(self, field: str, desc: bool = False):
        """Mock order by."""
        self._order_field = (field, desc)
        return self
    
    def insert(self, data: Dict[str, Any]):
        """Mock insert operation."""
        if self.name not in self.storage:
            self.storage[self.name] = []
        
        # Add default fields
        row = {
            'id': str(uuid4()),
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat(),
            **data
        }
        self.storage[self.name].append(row)
        return FakeSupabaseResult([row])
    
    def update(self, data: Dict[str, Any]):
        """Mock update operation."""
        return self
    
    def execute(self):
        """Mock execute operation."""
        if self.name not in self.storage:
            return FakeSupabaseResult([])
        
        results = list(self.storage[self.name])
        
        # Apply filters
        for filter_type, field, value in self._filters:
            if filter_type == 'eq':
                results = [r for r in results if r.get(field) == value]
            elif filter_type == 'in':
                results = [r for r in results if r.get(field) in value]
        
        # Apply ordering
        if self._order_field:
            field, desc = self._order_field
            results.sort(key=lambda x: x.get(field, ''), reverse=desc)
        
        # Reset state
        self._filters = []
        self._order_field = None
        
        return FakeSupabaseResult(results)


class FakeSupabaseClient:
    """Mock Supabase client for testing."""
    
    def __init__(self):
        self.storage: Dict[str, List[Dict[str, Any]]] = {}
        self._rpc_handlers: Dict[str, Any] = {
            'reserve_sambatan_slots': self._reserve_slots,
            'release_sambatan_slots': self._release_slots,
            'complete_sambatan_campaign': self._complete_campaign,
            'fail_sambatan_campaign': self._fail_campaign,
        }
    
    def table(self, name: str):
        """Get a table interface."""
        return FakeSupabaseTable(name, self.storage)
    
    def rpc(self, function_name: str, params: Dict[str, Any]):
        """Mock RPC function call."""
        handler = self._rpc_handlers.get(function_name)
        if handler:
            return handler(params)
        raise NotImplementedError(f"RPC function {function_name} not implemented")
    
    def _reserve_slots(self, params: Dict[str, Any]):
        """Mock reserve_sambatan_slots function."""
        campaign_id = params['p_campaign_id']
        slot_count = params['p_slot_count']
        
        campaigns = self.storage.get('sambatan_campaigns', [])
        campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
        
        if not campaign:
            raise Exception(f"Campaign not found: {campaign_id}")
        
        if campaign['status'] not in ['active', 'scheduled']:
            raise Exception("Campaign is not active")
        
        available = campaign['total_slots'] - campaign['filled_slots']
        if available < slot_count:
            raise Exception(f"Insufficient slots: available={available}, requested={slot_count}")
        
        campaign['filled_slots'] += slot_count
        if campaign['filled_slots'] >= campaign['total_slots']:
            campaign['status'] = 'locked'
        
        return FakeSupabaseResult([True])
    
    def _release_slots(self, params: Dict[str, Any]):
        """Mock release_sambatan_slots function."""
        campaign_id = params['p_campaign_id']
        slot_count = params['p_slot_count']
        
        campaigns = self.storage.get('sambatan_campaigns', [])
        campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
        
        if not campaign:
            raise Exception(f"Campaign not found: {campaign_id}")
        
        campaign['filled_slots'] = max(0, campaign['filled_slots'] - slot_count)
        if campaign['status'] == 'locked' and campaign['filled_slots'] < campaign['total_slots']:
            campaign['status'] = 'active'
        
        return FakeSupabaseResult([True])
    
    def _complete_campaign(self, params: Dict[str, Any]):
        """Mock complete_sambatan_campaign function."""
        campaign_id = params['p_campaign_id']
        
        campaigns = self.storage.get('sambatan_campaigns', [])
        campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
        
        if campaign:
            campaign['status'] = 'fulfilled'
            campaign['fulfilled_at'] = datetime.now(UTC).isoformat()
        
        # Update participants
        participants = self.storage.get('sambatan_participants', [])
        for p in participants:
            if p['campaign_id'] == campaign_id and p['status'] == 'pending_payment':
                p['status'] = 'confirmed'
                p['confirmed_at'] = datetime.now(UTC).isoformat()
        
        return FakeSupabaseResult([True])
    
    def _fail_campaign(self, params: Dict[str, Any]):
        """Mock fail_sambatan_campaign function."""
        campaign_id = params['p_campaign_id']
        
        campaigns = self.storage.get('sambatan_campaigns', [])
        campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
        
        if campaign:
            campaign['status'] = 'expired'
            campaign['cancelled_at'] = datetime.now(UTC).isoformat()
        
        # Update participants
        participants = self.storage.get('sambatan_participants', [])
        for p in participants:
            if p['campaign_id'] == campaign_id and p['status'] in ['pending_payment', 'confirmed']:
                p['status'] = 'refunded'
        
        return FakeSupabaseResult([True])


@pytest.fixture
def fake_supabase_client() -> FakeSupabaseClient:
    """Provide a fake Supabase client for testing."""
    return FakeSupabaseClient()
