# algorithms/collaborative_filtering.py
import time
import logging
from typing import Dict, List, Tuple, Optional, Set, Any, DefaultDict
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from src.models.cultural_models import CulturalContext, CraftType, IndianRegion, Festival
from src.models.recommendation_models import UserInteractionFeedback
from src.utils.cultural_analyzer import CulturalKnowledgeBase

logger = logging.getLogger(__name__)

@dataclass
class UserCulturalProfile:
    """Cultural preference profile for a user"""
    preferred_craft_types: Dict[CraftType, float]  # Craft type -> preference score
    preferred_regions: Dict[IndianRegion, float]   # Region -> preference score
    preferred_festivals: Dict[Festival, float]     # Festival -> preference score
    preferred_materials: Dict[str, float]          # Material -> preference score
    seasonal_patterns: Dict[int, float]            # Month -> activity score
    cultural_openness: float                       # Willingness to explore new cultures (0-1)
    traditional_preference: float                  # Traditional vs contemporary preference (0-1)
    interaction_count: int
    last_updated: datetime

@dataclass
class ItemSimilarityScore:
    """Similarity between two items from collaborative perspective"""
    user_overlap_count: int
    preference_correlation: float
    cultural_affinity: float
    seasonal_alignment: float
    overall_similarity: float

class CulturalCollaborativeFilter:
    """
    Collaborative filtering with cultural intelligence
    Learns user preferences while respecting cultural context and diversity
    """
    
    def __init__(self):
        self.knowledge_base = CulturalKnowledgeBase()
        
        # User data storage (in production, this would be in a database)
        self.user_profiles: Dict[str, UserCulturalProfile] = {}
        self.user_interactions: DefaultDict[str, List[UserInteractionFeedback]] = defaultdict(list)
        self.item_interactions: DefaultDict[str, List[UserInteractionFeedback]] = defaultdict(list)
        
        # Similarity matrices (cached for performance)
        self.user_similarity_cache: Dict[Tuple[str, str], float] = {}
        self.item_similarity_cache: Dict[Tuple[str, str], ItemSimilarityScore] = {}
        
        # Configuration
        self.min_interactions_for_profile = 3
        self.similarity_cache_ttl = 3600  # 1 hour
        self.cultural_diversity_bonus = 0.1
        self.traditional_craft_bonus = 0.05
        
        # Performance tracking
        self.stats = {
            "profiles_created": 0,
            "interactions_processed": 0,
            "recommendations_generated": 0,
            "cultural_discoveries_promoted": 0,
            "avg_cultural_diversity": 0.0
        }
        
        logger.info("Cultural Collaborative Filter initialized")

    def record_user_interaction(self, feedback: UserInteractionFeedback):
        """Record user interaction for learning preferences"""
        try:
            user_id = feedback.user_id or "anonymous"
            
            # Store interaction
            self.user_interactions[user_id].append(feedback)
            self.item_interactions[feedback.recommended_item_id].append(feedback)
            
            # Update user profile
            self._update_user_profile(user_id, feedback)
            
            # Clear similarity cache for affected user
            self._clear_user_similarity_cache(user_id)
            
            self.stats["interactions_processed"] += 1
            
            logger.debug(f"Recorded interaction: {user_id} -> {feedback.recommended_item_id} ({feedback.interaction_type})")
            
        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")

    def get_user_cultural_profile(self, user_id: str) -> Optional[UserCulturalProfile]:
        """Get or create user cultural profile"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # Create new profile if user has enough interactions
        interactions = self.user_interactions.get(user_id, [])
        if len(interactions) >= self.min_interactions_for_profile:
            profile = self._create_user_profile(user_id, interactions)
            self.user_profiles[user_id] = profile
            self.stats["profiles_created"] += 1
            return profile
        
        return None

    def find_similar_users(self, target_user_id: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Find users with similar cultural preferences"""
        target_profile = self.get_user_cultural_profile(target_user_id)
        if not target_profile:
            return []
        
        similar_users = []
        
        for user_id, profile in self.user_profiles.items():
            if user_id == target_user_id:
                continue
            
            # Calculate cultural similarity
            similarity = self._calculate_user_cultural_similarity(target_profile, profile)
            if similarity > 0.1:  # Minimum similarity threshold
                similar_users.append((user_id, similarity))
        
        # Sort by similarity and limit
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return similar_users[:limit]

    def get_collaborative_recommendations(
        self, 
        user_id: str, 
        available_items: List[Dict[str, Any]], 
        limit: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Generate collaborative recommendations with cultural awareness"""
        
        user_profile = self.get_user_cultural_profile(user_id)
        if not user_profile:
            logger.info(f"No profile available for user {user_id}, using content-based fallback")
            return self._content_based_fallback(available_items, limit)
        
        # Find similar users
        similar_users = self.find_similar_users(user_id, limit=20)
        if not similar_users:
            return self._content_based_fallback(available_items, limit)
        
        # Collect items liked by similar users
        candidate_scores = defaultdict(float)
        candidate_cultural_matches = defaultdict(list)
        
        for similar_user_id, similarity_score in similar_users:
            user_interactions = self.user_interactions[similar_user_id]
            
            for interaction in user_interactions:
                # Only consider positive interactions
                if self._is_positive_interaction(interaction):
                    item_id = interaction.recommended_item_id
                    
                    # Find item in available items
                    item_data = self._find_item_by_id(item_id, available_items)
                    if item_data:
                        # Score based on interaction strength and user similarity
                        interaction_weight = self._get_interaction_weight(interaction)
                        score = similarity_score * interaction_weight
                        
                        candidate_scores[item_id] += score
                        candidate_cultural_matches[item_id].append(similar_user_id)
        
        # Apply cultural diversity bonus
        for item_id in candidate_scores:
            item_data = self._find_item_by_id(item_id, available_items)
            if item_data and item_data.get("cultural_context"):
                diversity_bonus = self._calculate_cultural_diversity_bonus(
                    item_data["cultural_context"], user_profile
                )
                candidate_scores[item_id] += diversity_bonus
        
        # Convert to recommendations
        recommendations = []
        for item_id, score in candidate_scores.items():
            item_data = self._find_item_by_id(item_id, available_items)
            if item_data:
                recommendations.append((item_data, score))
        
        # Sort and limit
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        self.stats["recommendations_generated"] += 1
        
        return recommendations[:limit]

    def predict_user_item_rating(
        self, 
        user_id: str, 
        item_cultural_context: CulturalContext
    ) -> float:
        """Predict how much a user would like an item based on cultural context"""
        
        user_profile = self.get_user_cultural_profile(user_id)
        if not user_profile:
            return 0.5  # Neutral rating
        
        rating = 0.0
        
        # Craft type preference
        if item_cultural_context.craft_type:
            craft_preference = user_profile.preferred_craft_types.get(
                item_cultural_context.craft_type, 0.0
            )
            rating += craft_preference * 0.3
        
        # Regional preference
        if item_cultural_context.region:
            region_preference = user_profile.preferred_regions.get(
                item_cultural_context.region, 0.0
            )
            rating += region_preference * 0.25
        
        # Festival relevance
        for festival in item_cultural_context.festival_relevance:
            festival_preference = user_profile.preferred_festivals.get(festival, 0.0)
            rating += festival_preference * 0.15
        
        # Material preferences
        for material in item_cultural_context.materials:
            material_preference = user_profile.preferred_materials.get(material, 0.0)
            rating += material_preference * 0.1
        
        # Traditional vs contemporary alignment
        if item_cultural_context.cultural_tags:
            traditional_indicators = ["traditional", "heritage", "ancestral", "authentic"]
            is_traditional = any(tag in traditional_indicators for tag in item_cultural_context.cultural_tags)
            
            if is_traditional:
                rating += user_profile.traditional_preference * 0.1
            else:
                rating += (1 - user_profile.traditional_preference) * 0.1
        
        # Cultural openness bonus for diverse items
        if self._is_culturally_diverse_for_user(item_cultural_context, user_profile):
            rating += user_profile.cultural_openness * 0.1
        
        return min(rating, 1.0)  # Cap at 1.0

    # Private helper methods

    def _update_user_profile(self, user_id: str, feedback: UserInteractionFeedback):
        """Update user profile based on new interaction"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            # Create new profile if enough interactions exist
            interactions = self.user_interactions[user_id]
            if len(interactions) >= self.min_interactions_for_profile:
                profile = self._create_user_profile(user_id, interactions)
                self.user_profiles[user_id] = profile
        else:
            # Update existing profile
            self._incremental_profile_update(profile, feedback)

    def _create_user_profile(self, user_id: str, interactions: List[UserInteractionFeedback]) -> UserCulturalProfile:
        """Create user cultural profile from interaction history"""
        craft_scores = defaultdict(float)
        region_scores = defaultdict(float)
        festival_scores = defaultdict(float)
        material_scores = defaultdict(float)
        monthly_activity = defaultdict(float)
        
        traditional_score = 0.0
        total_interactions = len(interactions)
        positive_interactions = 0
        
        for interaction in interactions:
            weight = self._get_interaction_weight(interaction)
            
            if self._is_positive_interaction(interaction):
                positive_interactions += 1
                
                # Extract cultural context if available
                # In practice, you'd fetch this from your database
                # For now, we'll simulate based on cultural match accuracy
                if interaction.cultural_match_accuracy and interaction.cultural_match_accuracy > 0.5:
                    # Simulate cultural preferences based on interaction
                    # This would be replaced with actual cultural context from the item
                    pass
            
            # Track monthly activity
            month = interaction.timestamp.month
            monthly_activity[month] += weight
        
        # Calculate cultural openness (willingness to try diverse items)
        cultural_openness = min(positive_interactions / max(total_interactions, 1), 1.0)
        
        # Calculate traditional preference
        traditional_preference = traditional_score / max(total_interactions, 1)
        
        return UserCulturalProfile(
            preferred_craft_types=dict(craft_scores),
            preferred_regions=dict(region_scores),
            preferred_festivals=dict(festival_scores),
            preferred_materials=dict(material_scores),
            seasonal_patterns=dict(monthly_activity),
            cultural_openness=cultural_openness,
            traditional_preference=traditional_preference,
            interaction_count=total_interactions,
            last_updated=datetime.now()
        )

    def _incremental_profile_update(self, profile: UserCulturalProfile, feedback: UserInteractionFeedback):
        """Incrementally update profile with new feedback"""
        learning_rate = 0.1  # How quickly to adapt to new information
        
        if self._is_positive_interaction(feedback):
            # Increase preferences based on positive interaction
            # This would be enhanced with actual cultural context from the item
            pass
        
        profile.interaction_count += 1
        profile.last_updated = datetime.now()

    def _calculate_user_cultural_similarity(
        self, 
        profile1: UserCulturalProfile, 
        profile2: UserCulturalProfile
    ) -> float:
        """Calculate cultural similarity between two user profiles"""
        
        similarities = []
        
        # Craft type similarity
        craft_sim = self._calculate_preference_similarity(
            profile1.preferred_craft_types, profile2.preferred_craft_types
        )
        similarities.append(craft_sim * 0.3)
        
        # Regional similarity
        region_sim = self._calculate_preference_similarity(
            profile1.preferred_regions, profile2.preferred_regions
        )
        similarities.append(region_sim * 0.25)
        
        # Festival similarity
        festival_sim = self._calculate_preference_similarity(
            profile1.preferred_festivals, profile2.preferred_festivals
        )
        similarities.append(festival_sim * 0.2)
        
        # Traditional preference alignment
        trad_sim = 1.0 - abs(profile1.traditional_preference - profile2.traditional_preference)
        similarities.append(trad_sim * 0.15)
        
        # Cultural openness similarity
        openness_sim = 1.0 - abs(profile1.cultural_openness - profile2.cultural_openness)
        similarities.append(openness_sim * 0.1)
        
        return sum(similarities)

    def _calculate_preference_similarity(self, prefs1: Dict, prefs2: Dict) -> float:
        """Calculate similarity between two preference dictionaries"""
        if not prefs1 or not prefs2:
            return 0.0
        
        # Get all keys from both dictionaries
        all_keys = set(prefs1.keys()) | set(prefs2.keys())
        if not all_keys:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(prefs1.get(key, 0) * prefs2.get(key, 0) for key in all_keys)
        norm1 = math.sqrt(sum(score**2 for score in prefs1.values()))
        norm2 = math.sqrt(sum(score**2 for score in prefs2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def _is_positive_interaction(self, interaction: UserInteractionFeedback) -> bool:
        """Determine if an interaction is positive"""
        positive_types = ["click", "view", "purchase", "like", "save"]
        return interaction.interaction_type in positive_types or (
            interaction.explicit_rating and interaction.explicit_rating >= 3.0
        )

    def _get_interaction_weight(self, interaction: UserInteractionFeedback) -> float:
        """Get weight for interaction based on type and duration"""
        type_weights = {
            "purchase": 1.0,
            "like": 0.8,
            "save": 0.7,
            "click": 0.5,
            "view": 0.3,
            "ignore": 0.0,
            "dislike": -0.3
        }
        
        base_weight = type_weights.get(interaction.interaction_type, 0.3)
        
        # Adjust based on interaction duration
        if interaction.interaction_duration_seconds:
            if interaction.interaction_duration_seconds > 30:
                base_weight *= 1.2  # Bonus for long engagement
            elif interaction.interaction_duration_seconds < 5:
                base_weight *= 0.8  # Penalty for brief interaction
        
        # Adjust based on explicit rating
        if interaction.explicit_rating:
            rating_multiplier = interaction.explicit_rating / 5.0
            base_weight *= rating_multiplier
        
        return max(base_weight, 0.0)

    def _calculate_cultural_diversity_bonus(
        self, 
        item_context: CulturalContext, 
        user_profile: UserCulturalProfile
    ) -> float:
        """Calculate bonus for culturally diverse recommendations"""
        diversity_bonus = 0.0
        
        # Bonus for exploring new regions
        if item_context.region:
            region_familiarity = user_profile.preferred_regions.get(item_context.region, 0.0)
            if region_familiarity < 0.3:  # Unfamiliar region
                diversity_bonus += self.cultural_diversity_bonus * user_profile.cultural_openness
                self.stats["cultural_discoveries_promoted"] += 1
        
        # Bonus for traditional crafts (cultural preservation)
        if item_context.cultural_tags:
            traditional_indicators = ["traditional", "heritage", "ancestral"]
            if any(tag in traditional_indicators for tag in item_context.cultural_tags):
                diversity_bonus += self.traditional_craft_bonus
        
        return diversity_bonus

    def _is_culturally_diverse_for_user(
        self, 
        item_context: CulturalContext, 
        user_profile: UserCulturalProfile
    ) -> bool:
        """Check if item represents cultural diversity for the user"""
        # Check if region is different from user's top preferences
        top_regions = sorted(
            user_profile.preferred_regions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        if item_context.region:
            user_top_region_scores = [score for region, score in top_regions if region == item_context.region]
            if not user_top_region_scores or user_top_region_scores[0] < 0.5:
                return True
        
        return False

    def _content_based_fallback(
        self, 
        available_items: List[Dict[str, Any]], 
        limit: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Fallback to content-based recommendations when collaborative data is insufficient"""
        # Simple popularity-based fallback
        # In practice, this would call your content-based recommender
        return [(item, 0.5) for item in available_items[:limit]]

    def _find_item_by_id(self, item_id: str, available_items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find item by ID in available items list"""
        for item in available_items:
            if item.get("id") == item_id:
                return item
        return None

    def _clear_user_similarity_cache(self, user_id: str):
        """Clear similarity cache entries involving a specific user"""
        keys_to_remove = [
            key for key in self.user_similarity_cache.keys() 
            if user_id in key
        ]
        for key in keys_to_remove:
            del self.user_similarity_cache[key]

    def get_user_preference_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about user's cultural preferences"""
        profile = self.get_user_cultural_profile(user_id)
        if not profile:
            return {"error": "No profile available"}

        # Get top preferences
        top_craft_types = sorted(
            profile.preferred_craft_types.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        top_regions = sorted(
            profile.preferred_regions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        top_festivals = sorted(
            profile.preferred_festivals.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]

        return {
            "user_id": user_id,
            "profile_maturity": min(profile.interaction_count / 20, 1.0),  # 0-1 scale
            "cultural_openness": profile.cultural_openness,
            "traditional_preference": profile.traditional_preference,
            "top_craft_preferences": [{"craft_type": ct.value, "score": score} for ct, score in top_craft_types],
            "top_region_preferences": [{"region": r.value, "score": score} for r, score in top_regions],
            "top_festival_preferences": [{"festival": f.value, "score": score} for f, score in top_festivals],
            "total_interactions": profile.interaction_count,
            "last_updated": profile.last_updated.isoformat(),
            "seasonal_patterns": dict(profile.seasonal_patterns)
        }

    def get_collaborative_stats(self) -> Dict[str, Any]:
        """Get collaborative filtering statistics"""
        total_users = len(self.user_profiles)
        total_interactions = sum(len(interactions) for interactions in self.user_interactions.values())
        
        # Calculate average cultural diversity
        if total_users > 0:
            diversity_scores = []
            for profile in self.user_profiles.values():
                region_diversity = len(profile.preferred_regions) / max(len(IndianRegion), 1)
                craft_diversity = len(profile.preferred_craft_types) / max(len(CraftType), 1)
                diversity_scores.append((region_diversity + craft_diversity) / 2)
            
            avg_diversity = sum(diversity_scores) / len(diversity_scores)
            self.stats["avg_cultural_diversity"] = avg_diversity

        return {
            **self.stats,
            "total_user_profiles": total_users,
            "total_interactions": total_interactions,
            "cache_sizes": {
                "user_similarity": len(self.user_similarity_cache),
                "item_similarity": len(self.item_similarity_cache)
            },
            "avg_interactions_per_user": total_interactions / max(total_users, 1)
        }

    def clear_cache(self):
        """Clear all collaborative filtering caches"""
        self.user_similarity_cache.clear()
        self.item_similarity_cache.clear()
        logger.info("Collaborative filtering caches cleared")

# Global instance
collaborative_filter = CulturalCollaborativeFilter()