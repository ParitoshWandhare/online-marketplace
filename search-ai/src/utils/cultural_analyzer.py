# utils/cultural_analyzer.py
from typing import Dict, List, Set, Any
from src.models.cultural_models import CraftType, IndianRegion, Festival, CulturalSignificance

class CulturalKnowledgeBase:
    """
    Comprehensive knowledge base for Indian cultural context detection
    Contains taxonomies, keywords, and patterns for AI-assisted cultural analysis
    """
    
    def __init__(self):
        self.craft_keywords = self._initialize_craft_keywords()
        self.material_keywords = self._initialize_material_keywords()
        self.technique_keywords = self._initialize_technique_keywords()
        self.regional_keywords = self._initialize_regional_keywords()
        self.festival_keywords = self._initialize_festival_keywords()
        self.cultural_significance_keywords = self._initialize_cultural_significance_keywords()
        
    def _initialize_craft_keywords(self) -> Dict[str, List[str]]:
        """Comprehensive craft type detection keywords"""
        return {
            CraftType.POTTERY.value: [
                "pottery", "ceramic", "clay", "pot", "vase", "earthenware", "terracotta", 
                "stoneware", "porcelain", "mitti", "kulhar", "matka", "ghada", "surahi", 
                "kalash", "diya", "planter", "bowl", "pitcher", "urn", "fired", "glazed",
                "wheel thrown", "hand thrown", "kiln", "blue pottery", "black pottery"
            ],
            
            CraftType.TEXTILES.value: [
                "textile", "fabric", "cloth", "weaving", "embroidery", "saree", "kurta", 
                "dupatta", "shawl", "silk", "cotton", "handloom", "khadi", "chikankari",
                "kantha", "phulkari", "bandhani", "tie dye", "block print", "batik",
                "ikat", "chanderi", "banarasi", "jamdani", "kalamkari", "ajrakh",
                "thread work", "zardozi", "mirror work", "applique", "patchwork"
            ],
            
            CraftType.JEWELRY.value: [
                "jewelry", "jewellery", "necklace", "earrings", "bracelet", "ring",
                "pendant", "anklet", "nose ring", "gold", "silver", "kundan", "meenakari",
                "filigree", "tribal jewelry", "temple jewelry", "oxidized", "beaded",
                "stone jewelry", "pearl", "coral", "turquoise", "jhumka", "choker",
                "bangles", "kadas", "maang tikka", "traditional jewelry"
            ],
            
            CraftType.WOODWORK.value: [
                "wood", "wooden", "carving", "sculpture", "furniture", "teak", "rosewood",
                "sandalwood", "sheesham", "mango wood", "carved", "inlay", "marquetry",
                "jali work", "lattice", "chair", "table", "chest", "box", "frame",
                "figurine", "statue", "totem", "mask", "panel", "screen", "cabinet"
            ],
            
            CraftType.METALCRAFT.value: [
                "metal", "brass", "copper", "bronze", "iron", "steel", "aluminium",
                "dhokra", "dokra", "lost wax", "casting", "engraving", "embossing",
                "repoussé", "filigree", "bidriware", "damascening", "utensils", "vessels",
                "lamp", "diya", "plate", "bowl", "figurine", "bell", "gong"
            ],
            
            CraftType.PAINTING.value: [
                "painting", "miniature", "madhubani", "warli", "pattachitra", "tanjore",
                "mughal", "rajasthani", "pahari", "pichwai", "gond", "tribal art",
                "folk art", "canvas", "paper", "palm leaf", "tempera", "watercolor",
                "acrylic", "oil", "natural pigments", "gold leaf", "religious painting"
            ],
            
            CraftType.SCULPTURE.value: [
                "sculpture", "statue", "carving", "stone", "marble", "granite", "sandstone",
                "bronze casting", "terracotta sculpture", "clay sculpture", "relief",
                "figurine", "bust", "deity", "dancing figure", "animal sculpture",
                "architectural sculpture", "garden sculpture", "decorative sculpture"
            ],
            
            CraftType.LEATHER_WORK.value: [
                "leather", "hide", "skin", "bag", "purse", "wallet", "belt", "shoes",
                "sandals", "mojari", "kolhapuri", "tooled leather", "embossed leather",
                "painted leather", "stitched", "hand crafted leather", "buffalo leather"
            ],
            
            CraftType.BAMBOO_CRAFT.value: [
                "bamboo", "cane", "rattan", "wicker", "basket", "mat", "furniture",
                "screen", "lampshade", "decorative items", "utility items", "weaving",
                "split bamboo", "bamboo craft", "cane work", "basketry", "storage basket"
            ],
            
            CraftType.STONE_CARVING.value: [
                "stone", "marble", "granite", "sandstone", "carving", "sculpture",
                "relief", "inlay", "pietra dura", "stone work", "architectural element",
                "garden sculpture", "temple carving", "decorative stone", "carved panel"
            ],
            
            CraftType.GLASS_WORK.value: [
                "glass", "crystal", "blown glass", "stained glass", "fused glass",
                "glass painting", "mirror work", "glass bead", "decorative glass",
                "glass sculpture", "glass vessel", "glass ornament", "etched glass"
            ],
            
            CraftType.PAPER_CRAFT.value: [
                "paper", "papier mache", "origami", "quilling", "paper sculpture",
                "handmade paper", "paper mache", "paper art", "paper cutting",
                "paper flowers", "greeting cards", "paper jewelry", "book binding"
            ]
        }

    def _initialize_festival_keywords(self) -> Dict[str, List[str]]:
        """Festival and seasonal keywords"""
        return {
            Festival.DIWALI.value: [
                "diwali", "deepavali", "festival of lights", "diya", "rangoli", "lakshmi",
                "oil lamp", "decorative lights", "sweets", "gifts", "celebration",
                "traditional decor", "festive", "prosperity", "wealth", "fortune"
            ],
            Festival.HOLI.value: [
                "holi", "festival of colors", "colors", "gulal", "spring festival",
                "celebration", "joy", "vibrant", "colorful", "traditional colors",
                "natural colors", "herbal colors", "festive celebration"
            ],
            Festival.DUSSEHRA.value: [
                "dussehra", "vijayadashami", "durga puja", "navratri", "goddess durga",
                "victory", "good over evil", "traditional celebration", "festive decor",
                "religious celebration", "autumn festival"
            ],
            Festival.NAVRATRI.value: [
                "navratri", "nine nights", "durga", "goddess", "dance", "garba", "dandiya",
                "traditional dance", "festive wear", "colorful clothes", "celebration",
                "religious festival", "traditional music"
            ],
            Festival.GANESH_CHATURTHI.value: [
                "ganesh chaturthi", "ganesha", "elephant god", "modak", "eco-friendly",
                "clay ganesh", "festival celebration", "traditional sweets", "religious",
                "mumbai festival", "community celebration"
            ],
            Festival.KARVA_CHAUTH.value: [
                "karva chauth", "married women", "fasting", "moon", "traditional ritual",
                "karva", "water pot", "henna", "mehendi", "traditional ceremony",
                "north indian festival", "love", "devotion"
            ],
            Festival.RAKSHA_BANDHAN.value: [
                "raksha bandhan", "rakhi", "brother sister", "protection", "thread",
                "traditional thread", "sibling love", "family festival", "august festival",
                "traditional celebration", "bond", "relationship"
            ],
            Festival.DHANTERAS.value: [
                "dhanteras", "dhan teras", "wealth", "prosperity", "gold", "silver",
                "buying gold", "lakshmi", "money", "fortune", "auspicious",
                "traditional purchase", "pre-diwali"
            ],
            Festival.CHRISTMAS.value: [
                "christmas", "xmas", "winter festival", "december", "gifts", "celebration",
                "festive season", "holiday", "christian festival", "decorations",
                "christmas tree", "santa", "winter celebration"
            ],
            Festival.EID.value: [
                "eid", "eid ul fitr", "eid ul adha", "islamic festival", "muslim festival",
                "celebration", "feast", "traditional sweets", "community", "religious",
                "crescent moon", "festive celebration"
            ],
            Festival.WEDDING_SEASON.value: [
                "wedding", "marriage", "bridal", "groom", "ceremony", "traditional wedding",
                "indian wedding", "wedding gifts", "trousseau", "celebration",
                "auspicious", "wedding season", "matrimony", "union"
            ]
        }

    def _initialize_cultural_significance_keywords(self) -> Dict[str, List[str]]:
        """Cultural significance detection keywords"""
        return {
            CulturalSignificance.CEREMONIAL.value: [
                "ceremonial", "ritual", "sacred", "worship", "temple", "prayer",
                "religious ceremony", "traditional ritual", "spiritual", "holy"
            ],
            CulturalSignificance.FESTIVAL_ITEM.value: [
                "festival", "celebration", "festive", "seasonal", "special occasion",
                "holiday", "traditional celebration", "community festival"
            ],
            CulturalSignificance.DAILY_USE.value: [
                "daily use", "everyday", "utility", "functional", "practical",
                "household", "kitchen", "home", "regular use", "utilitarian"
            ],
            CulturalSignificance.DECORATIVE.value: [
                "decorative", "ornamental", "display", "showcase", "aesthetic",
                "beautiful", "artistic", "home decor", "interior", "decoration"
            ],
            CulturalSignificance.RELIGIOUS.value: [
                "religious", "spiritual", "divine", "god", "goddess", "deity",
                "temple", "shrine", "worship", "prayer", "sacred", "holy"
            ],
            CulturalSignificance.WEDDING_ITEM.value: [
                "wedding", "bridal", "marriage", "matrimony", "bride", "groom",
                "wedding gift", "trousseau", "wedding ceremony", "nuptial"
            ],
            CulturalSignificance.GIFT_ITEM.value: [
                "gift", "present", "souvenir", "memento", "keepsake",
                "special gift", "traditional gift", "corporate gift", "return gift"
            ],
            CulturalSignificance.HERITAGE_PIECE.value: [
                "heritage", "traditional", "antique", "vintage", "classic",
                "ancestral", "family heirloom", "cultural heritage", "historical"
            ]
        }

    def get_cultural_categories(self) -> Dict[str, List[str]]:
        """Get all available cultural categories"""
        return {
            "craft_types": [craft.value for craft in CraftType],
            "regions": [region.value for region in IndianRegion],
            "festivals": [festival.value for festival in Festival],
            "cultural_significance": [sig.value for sig in CulturalSignificance]
        }

    def get_seasonal_keywords(self, festivals: List[Festival]) -> List[str]:
        """Get seasonal keywords for given festivals"""
        keywords = []
        for festival in festivals:
            if festival.value in self.festival_keywords:
                keywords.extend(self.festival_keywords[festival.value][:5])  # Top 5 keywords
        return list(set(keywords))  # Remove duplicates

    def detect_craft_type_confidence(self, text: str) -> Dict[str, float]:
        """Detect craft types with confidence scores"""
        text_lower = text.lower()
        confidence_scores = {}
        
        for craft_type, keywords in self.craft_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                # Confidence based on number of matches and keyword specificity
                confidence = min(matches * 0.2, 1.0)
                confidence_scores[craft_type] = confidence
        
        return confidence_scores

    def detect_regional_influence(self, text: str) -> Dict[str, float]:
        """Detect regional influences with confidence scores"""
        text_lower = text.lower()
        confidence_scores = {}
        
        for region, keywords in self.regional_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                confidence = min(matches * 0.3, 1.0)  # Regional keywords are more specific
                confidence_scores[region] = confidence
        
        return confidence_scores

    def extract_materials(self, text: str) -> List[str]:
        """Extract materials mentioned in text"""
        text_lower = text.lower()
        detected_materials = []
        
        for category, materials in self.material_keywords.items():
            for material in materials:
                if material in text_lower:
                    detected_materials.append(material)
        
        return list(set(detected_materials))  # Remove duplicates

    def extract_techniques(self, text: str) -> List[str]:
        """Extract traditional techniques mentioned in text"""
        text_lower = text.lower()
        detected_techniques = []
        
        for category, techniques in self.technique_keywords.items():
            for technique in techniques:
                if technique in text_lower:
                    detected_techniques.append(technique)
        
        return list(set(detected_techniques))  # Remove duplicates

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        total_keywords = sum(len(keywords) for keywords in self.craft_keywords.values())
        total_materials = sum(len(materials) for materials in self.material_keywords.values())
        total_techniques = sum(len(techniques) for techniques in self.technique_keywords.values())
        total_regional = sum(len(keywords) for keywords in self.regional_keywords.values())
        total_festivals = sum(len(keywords) for keywords in self.festival_keywords.values())
        
        return {
            "total_craft_keywords": total_keywords,
            "total_material_keywords": total_materials,
            "total_technique_keywords": total_techniques,
            "total_regional_keywords": total_regional,
            "total_festival_keywords": total_festivals,
            "craft_types_covered": len(self.craft_keywords),
            "regions_covered": len(self.regional_keywords),
            "festivals_covered": len(self.festival_keywords)
        }

    def validate_cultural_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich cultural context"""
        validated = context.copy()
        
        # Ensure craft type is valid
        if "craft_type" in validated:
            if validated["craft_type"] not in [craft.value for craft in CraftType]:
                validated["craft_type"] = CraftType.UNKNOWN.value
        
        # Ensure region is valid
        if "region" in validated:
            if validated["region"] not in [region.value for region in IndianRegion]:
                validated["region"] = IndianRegion.UNKNOWN.value
        
        # Validate festivals
        if "festival_relevance" in validated:
            valid_festivals = [festival.value for festival in Festival]
            validated["festival_relevance"] = [
                f for f in validated["festival_relevance"] 
                if f in valid_festivals
            ]
        
        return validated

    def _initialize_material_keywords(self) -> Dict[str, List[str]]:
        """Material detection keywords organized by craft type"""
        return {
            "clay_materials": [
                "clay", "terracotta", "ceramic", "porcelain", "stoneware", "earthenware",
                "red clay", "white clay", "potter clay", "firing clay", "glazed ceramic"
            ],
            "textile_materials": [
                "cotton", "silk", "wool", "linen", "jute", "hemp", "khadi", "handspun",
                "organic cotton", "raw silk", "tussar silk", "mulberry silk", "cashmere",
                "merino wool", "yak wool", "natural fiber", "synthetic fiber"
            ],
            "metal_materials": [
                "gold", "silver", "brass", "copper", "bronze", "iron", "steel", "aluminum",
                "white metal", "german silver", "oxidized silver", "sterling silver",
                "pure gold", "gold plated", "brass antique", "copper antique"
            ],
            "wood_materials": [
                "teak", "rosewood", "sandalwood", "sheesham", "mango wood", "pine",
                "oak", "bamboo", "cane", "rattan", "mahogany", "cedar", "walnut",
                "reclaimed wood", "sustainable wood", "hardwood", "softwood"
            ],
            "stone_materials": [
                "marble", "granite", "sandstone", "limestone", "slate", "quartzite",
                "soapstone", "jade", "onyx", "semi-precious stones", "precious stones",
                "natural stone", "carved stone", "polished stone"
            ],
            "natural_materials": [
                "coconut shell", "seeds", "beads", "pearls", "coral", "shells",
                "bone", "horn", "leather", "hide", "natural dyes", "vegetable dyes",
                "mineral pigments", "organic materials", "eco-friendly"
            ]
        }

    def _initialize_technique_keywords(self) -> Dict[str, List[str]]:
        """Traditional technique keywords"""
        return {
            "pottery_techniques": [
                "wheel throwing", "hand throwing", "coiling", "slab building", "glazing",
                "firing", "kiln firing", "pit firing", "burnishing", "slip trailing",
                "sgraffito", "raku", "traditional firing", "wood firing"
            ],
            "textile_techniques": [
                "hand weaving", "block printing", "screen printing", "tie dye", "batik",
                "embroidery", "applique", "patchwork", "quilting", "knitting", "crochet",
                "spinning", "natural dyeing", "indigo dyeing", "resist dyeing"
            ],
            "metalwork_techniques": [
                "casting", "forging", "engraving", "embossing", "chasing", "repoussé",
                "filigree", "granulation", "lost wax casting", "sand casting",
                "hand hammering", "planishing", "patination", "oxidation"
            ],
            "woodwork_techniques": [
                "carving", "turning", "joinery", "marquetry", "inlay", "burning",
                "staining", "polishing", "hand finishing", "traditional joinery",
                "mortise and tenon", "dovetail", "relief carving", "chip carving"
            ],
            "general_techniques": [
                "handmade", "hand crafted", "traditional", "artisanal", "bespoke",
                "custom made", "one of a kind", "handwoven", "hand painted",
                "hand carved", "hand forged", "hand finished", "traditional methods"
            ]
        }

    def _initialize_regional_keywords(self) -> Dict[str, List[str]]:
        """Regional style and origin keywords"""
        return {
            IndianRegion.RAJASTHAN.value: [
                "rajasthani", "jaipur", "jodhpur", "udaipur", "bikaner", "blue pottery",
                "lac work", "mirror work", "bandhani", "leheriya", "gota work",
                "rajasthani embroidery", "camel bone", "makrana marble", "desert craft"
            ],
            IndianRegion.GUJARAT.value: [
                "gujarati", "kutch", "ahmedabad", "surat", "vadodara", "ajrakh",
                "bandhani", "patola", "rogan art", "abhla embroidery", "kutch embroidery",
                "block printing", "natural dyes", "tribal craft", "mirror work"
            ],
            IndianRegion.WEST_BENGAL.value: [
                "bengali", "kolkata", "kantha", "dokra", "shola craft", "conch shell",
                "terracotta", "jamdani", "tant saree", "baluchari", "clay dolls",
                "durga idols", "bamboo craft", "jute craft", "hand painted"
            ],
            IndianRegion.TAMIL_NADU.value: [
                "tamil", "chennai", "madurai", "tanjore painting", "bronze casting",
                "kanchipuram silk", "temple jewelry", "stone carving", "wood carving",
                "pottery", "palm leaf", "banana fiber", "coconut shell craft"
            ],
            IndianRegion.KERALA.value: [
                "kerala", "kochi", "coconut shell", "coir craft", "bamboo craft",
                "wood carving", "metal mirror", "kasavu saree", "traditional lamp",
                "boat making", "spice containers", "ayurvedic products"
            ],
            IndianRegion.MAHARASHTRA.value: [
                "maharashtrian", "mumbai", "pune", "kolhapur", "warli painting",
                "paithani", "kolhapuri chappal", "bidriware", "leather craft",
                "traditional pottery", "bamboo craft", "tribal art"
            ],
            IndianRegion.UTTAR_PRADESH.value: [
                "up", "lucknow", "varanasi", "agra", "chikankari", "zardozi",
                "carpet weaving", "brass work", "marble inlay", "wood carving",
                "glass work", "pottery", "traditional embroidery"
            ],
            IndianRegion.PUNJAB.value: [
                "punjabi", "amritsar", "chandigarh", "phulkari", "punjabi juti",
                "wood work", "metal craft", "traditional embroidery", "handloom",
                "wheat craft", "rural craft"
            ],
            IndianRegion.ODISHA.value: [
                "odia", "bhubaneswar", "puri", "pattachitra", "silver filigree",
                "stone carving", "wood carving", "palm leaf engraving", "applique work",
                "traditional painting", "temple craft", "tribal craft"
            ],
            IndianRegion.KARNATAKA.value: [
                "karnataka", "bangalore", "mysore", "channapatna toys", "rosewood craft",
                "sandalwood craft", "silk weaving", "bidriware", "wood inlay",
                "traditional painting", "stone craft"
            ],
            IndianRegion.ASSAM.value: [
                "assamese", "guwahati", "silk weaving", "bamboo craft", "cane craft",
                "traditional weaving", "tribal craft", "tea craft", "bell metal",
                "wood carving", "traditional textiles"
            ],
            IndianRegion.JAMMU_KASHMIR.value: [
                "kashmiri", "srinagar", "jammu", "paper mache", "carpet weaving",
                "pashmina", "wood carving", "copperware", "crewel embroidery",
                "traditional crafts", "walnut wood", "saffron craft"
            ]
        }