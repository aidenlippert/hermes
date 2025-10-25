"""
Agent-to-Agent Messaging Protocol

Enables autonomous conversations between agents across different businesses/contexts.
For example: Dentist office agent ↔ Insurance company agent
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Types of agent messages"""
    QUERY = "query"              # Ask for information
    RESPONSE = "response"        # Reply to query
    NOTIFICATION = "notification" # One-way update
    PROPOSAL = "proposal"        # Suggest action
    ACCEPTANCE = "acceptance"    # Accept proposal
    REJECTION = "rejection"      # Reject proposal
    TERMINATION = "termination"  # End conversation


class ConversationStatus(str, Enum):
    """Conversation lifecycle states"""
    ACTIVE = "active"
    AWAITING_RESPONSE = "awaiting_response"
    RESOLVED = "resolved"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Message:
    """A message between agents"""
    message_id: str
    conversation_id: str
    from_agent_id: str
    to_agent_id: str
    message_type: MessageType
    content: Dict[str, Any]
    requires_response: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return {
            **asdict(self),
            'message_type': self.message_type.value
        }


@dataclass
class Conversation:
    """A conversation thread between agents"""
    conversation_id: str
    participants: List[str]  # List of agent IDs
    topic: str
    status: ConversationStatus
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
    
    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value,
            'messages': [m.to_dict() for m in self.messages]
        }


class MessagingProtocol:
    """Manages agent-to-agent messaging"""
    
    def __init__(self):
        # In-memory storage
        self.conversations: Dict[str, Conversation] = {}
        self.messages: Dict[str, Message] = {}
        self.agent_inboxes: Dict[str, List[str]] = {}  # agent_id -> [message_ids]
        
        # Message handlers (agent_id -> handler function)
        self.handlers: Dict[str, Callable] = {}
    
    def register_agent(self, agent_id: str, handler: Callable):
        """Register agent message handler"""
        self.handlers[agent_id] = handler
        self.agent_inboxes[agent_id] = []
    
    async def start_conversation(
        self,
        initiator_id: str,
        target_id: str,
        topic: str,
        initial_message: Dict[str, Any]
    ) -> str:
        """Start new conversation between agents"""
        
        conv_id = str(uuid.uuid4())[:12]
        
        conversation = Conversation(
            conversation_id=conv_id,
            participants=[initiator_id, target_id],
            topic=topic,
            status=ConversationStatus.ACTIVE
        )
        
        self.conversations[conv_id] = conversation
        
        # Send initial message
        await self.send_message(
            conversation_id=conv_id,
            from_agent_id=initiator_id,
            to_agent_id=target_id,
            message_type=MessageType.QUERY,
            content=initial_message,
            requires_response=True
        )
        
        print(f"💬 Conversation started: {initiator_id} → {target_id} (topic: {topic})")
        return conv_id
    
    async def send_message(
        self,
        conversation_id: str,
        from_agent_id: str,
        to_agent_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        requires_response: bool = False
    ) -> str:
        """Send message in conversation"""
        
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        # Validate participants
        if from_agent_id not in conversation.participants:
            raise ValueError(f"Agent {from_agent_id} not in conversation")
        if to_agent_id not in conversation.participants:
            raise ValueError(f"Agent {to_agent_id} not in conversation")
        
        # Create message
        msg_id = str(uuid.uuid4())[:8]
        message = Message(
            message_id=msg_id,
            conversation_id=conversation_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            requires_response=requires_response
        )
        
        # Store message
        self.messages[msg_id] = message
        conversation.messages.append(message)
        
        # Add to recipient's inbox
        if to_agent_id in self.agent_inboxes:
            self.agent_inboxes[to_agent_id].append(msg_id)
        
        # Update conversation status
        if requires_response:
            conversation.status = ConversationStatus.AWAITING_RESPONSE
        
        # Deliver to agent
        if to_agent_id in self.handlers:
            await self.handlers[to_agent_id](message)
        
        print(f"📨 Message sent: {from_agent_id} → {to_agent_id} ({message_type.value})")
        
        # Auto-terminate check
        if message_type == MessageType.TERMINATION:
            await self._terminate_conversation(conversation_id)
        
        return msg_id
    
    async def _terminate_conversation(self, conversation_id: str):
        """Mark conversation as terminated"""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.status = ConversationStatus.TERMINATED
            conversation.resolved_at = datetime.now().isoformat()
            print(f"✅ Conversation terminated: {conversation_id}")
    
    async def check_termination(self, conversation_id: str) -> bool:
        """Check if conversation should be terminated
        
        Termination happens when:
        1. Explicit TERMINATION message sent
        2. All pending queries resolved
        3. Goal achieved (detected via metadata)
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False
        
        # Already terminated
        if conversation.status == ConversationStatus.TERMINATED:
            return True
        
        # Check if goal achieved (from metadata)
        if conversation.metadata.get("goal_achieved"):
            await self._terminate_conversation(conversation_id)
            return True
        
        # Check if all queries resolved
        pending_responses = [
            m for m in conversation.messages 
            if m.requires_response and m.message_type == MessageType.QUERY
        ]
        
        # Count responses
        responses = [
            m for m in conversation.messages
            if m.message_type == MessageType.RESPONSE
        ]
        
        if len(pending_responses) > 0 and len(responses) >= len(pending_responses):
            # All queries have responses
            await self._terminate_conversation(conversation_id)
            return True
        
        return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def get_agent_conversations(self, agent_id: str) -> List[Conversation]:
        """Get all conversations for agent"""
        return [
            conv for conv in self.conversations.values()
            if agent_id in conv.participants
        ]


# Global messaging protocol
messaging_protocol = MessagingProtocol()


# Example: Dentist office ↔ Insurance company
async def demo_dentist_insurance():
    """Demo: Autonomous conversation between dentist and insurance agents"""
    
    protocol = MessagingProtocol()
    
    # Insurance agent handler
    async def insurance_handler(message: Message):
        """Insurance agent processes messages"""
        print(f"🏥 Insurance agent received: {message.content}")
        
        if message.message_type == MessageType.QUERY:
            query = message.content.get("query")
            
            if "coverage" in query.lower():
                # Check coverage and respond
                await protocol.send_message(
                    conversation_id=message.conversation_id,
                    from_agent_id=message.to_agent_id,
                    to_agent_id=message.from_agent_id,
                    message_type=MessageType.RESPONSE,
                    content={
                        "status": "approved",
                        "coverage_amount": 1500.00,
                        "patient_responsibility": 300.00,
                        "authorization_code": "AUTH-12345"
                    }
                )
                
                # Mark goal achieved
                conv = protocol.get_conversation(message.conversation_id)
                if conv:
                    conv.metadata["goal_achieved"] = True
    
    # Dentist office agent handler
    async def dentist_handler(message: Message):
        """Dentist office agent processes messages"""
        print(f"🦷 Dentist agent received: {message.content}")
        
        if message.message_type == MessageType.RESPONSE:
            # Got insurance approval, send termination
            await protocol.send_message(
                conversation_id=message.conversation_id,
                from_agent_id=message.to_agent_id,
                to_agent_id=message.from_agent_id,
                message_type=MessageType.TERMINATION,
                content={"reason": "Authorization received, proceeding with treatment"}
            )
    
    # Register agents
    protocol.register_agent("dentist-agent-1", dentist_handler)
    protocol.register_agent("insurance-agent-1", insurance_handler)
    
    # Start conversation
    conv_id = await protocol.start_conversation(
        initiator_id="dentist-agent-1",
        target_id="insurance-agent-1",
        topic="Patient coverage verification",
        initial_message={
            "query": "Check coverage for root canal procedure",
            "patient_id": "P-67890",
            "procedure_code": "D3310",
            "estimated_cost": 1800.00
        }
    )
    
    # Wait for conversation to complete
    await asyncio.sleep(2)
    
    # Check termination
    terminated = await protocol.check_termination(conv_id)
    print(f"\n{'✅' if terminated else '⏳'} Conversation terminated: {terminated}")
    
    # Print conversation history
    conv = protocol.get_conversation(conv_id)
    if conv:
        print(f"\n📋 Conversation Summary:")
        print(f"  Topic: {conv.topic}")
        print(f"  Status: {conv.status.value}")
        print(f"  Messages: {len(conv.messages)}")
        for msg in conv.messages:
            print(f"    → {msg.from_agent_id} → {msg.to_agent_id}: {msg.message_type.value}")


# Example: Flight delay → Hotel notification
async def demo_flight_hotel_coordination():
    """Demo: Flight agent notifies hotel agent of delay"""
    
    protocol = MessagingProtocol()
    
    # Hotel agent handler
    async def hotel_handler(message: Message):
        """Hotel agent processes notifications"""
        print(f"🏨 Hotel agent received: {message.content}")
        
        if message.message_type == MessageType.NOTIFICATION:
            delay_info = message.content.get("delay_info")
            
            # Update reservation automatically
            await protocol.send_message(
                conversation_id=message.conversation_id,
                from_agent_id=message.to_agent_id,
                to_agent_id=message.from_agent_id,
                message_type=MessageType.RESPONSE,
                content={
                    "action": "check_in_time_updated",
                    "new_check_in": delay_info.get("new_arrival_time"),
                    "room_held": True,
                    "confirmation": "CONF-98765"
                }
            )
            
            # Terminate - notification handled
            await protocol.send_message(
                conversation_id=message.conversation_id,
                from_agent_id=message.to_agent_id,
                to_agent_id=message.from_agent_id,
                message_type=MessageType.TERMINATION,
                content={"reason": "Reservation updated successfully"}
            )
    
    # Flight agent handler
    async def flight_handler(message: Message):
        """Flight agent processes responses"""
        print(f"✈️ Flight agent received: {message.content}")
    
    # Register agents
    protocol.register_agent("flight-agent-1", flight_handler)
    protocol.register_agent("hotel-agent-1", hotel_handler)
    
    # Flight agent detects delay and notifies hotel
    conv_id = await protocol.start_conversation(
        initiator_id="flight-agent-1",
        target_id="hotel-agent-1",
        topic="Flight delay notification",
        initial_message={
            "delay_info": {
                "flight_number": "UA123",
                "original_arrival": "2025-10-25T14:00:00Z",
                "new_arrival_time": "2025-10-25T18:30:00Z",
                "delay_minutes": 270,
                "passenger_booking_id": "BOOK-12345"
            }
        }
    )
    
    # Wait for conversation
    await asyncio.sleep(2)
    
    # Check result
    conv = protocol.get_conversation(conv_id)
    if conv:
        print(f"\n📋 Flight-Hotel Coordination:")
        print(f"  Status: {conv.status.value}")
        print(f"  Messages exchanged: {len(conv.messages)}")


if __name__ == "__main__":
    print("🦷 Demo 1: Dentist ↔ Insurance\n")
    asyncio.run(demo_dentist_insurance())
    
    print("\n" + "="*60 + "\n")
    
    print("✈️ Demo 2: Flight delay → Hotel update\n")
    asyncio.run(demo_flight_hotel_coordination())
