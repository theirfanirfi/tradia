import asyncio
import aiohttp
import numpy as np
import pickle
import os
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from sklearn.metrics.pairwise import cosine_similarity
from enum import Enum

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "mxbai-embed-large:latest"
EMBEDDINGS_BASE_DIR = "embeddings_cache"

# Classification levels
class ClassificationLevel(str, Enum):
    SECTIONS = "sections"
    CHAPTERS = "chapters" 
    HEADINGS = "headings"
    SUB_HEADINGS = "sub_headings"

# Hierarchical label mappings
SECTION_MAP = {
    "Animals": "I",
    "Vegetables": "II",
    "Oils/Fats": "III",
    "Food/Drink": "IV",
    "Minerals": "V",
    "Chemicals": "VI",
    "Plastics/Rubber": "VII",
    "Leather/Furs": "VIII",
    "Woodwork": "IX",
    "Paper": "X",
    "Textiles": "XI",
    "Footwear/Wearables": "XII",
    "Stone/Ceramics": "XIII",
    "Jewellery": "XIV",
    "Metals": "XV",
    "Machinery/Electronics": "XVI",
    "Transport": "XVII",
    "Instruments": "XVIII",
    "Arms": "XIX",
    "Misc. Goods": "XX",
    "Art/Antiques": "XXI",
}

# Example structure for hierarchical mappings
HIERARCHICAL_MAPPINGS = {
  "I": {
    "chapters": {
      "Live animals": "1",
      "Meat and edible meat offal": "2",
      "Fish and crustaceans, molluscs and other aquatic invertebrates": "3",
      "Dairy produce; birds' eggs; natural honey; edible products of animal origin, not elsewhere specified or included": "4",
      "Products of animal origin, not elsewhere specified or included": "5"
    },
    
      "1": {
        "headings": {
          "LIVE HORSES, ASSES, MULES AND HINNIES": "0101",
          "LIVE BOVINE ANIMALS": "0102",
          "LIVE SWINE": "0103",
          "LIVE SHEEP AND GOATS": "0104",
          "LIVE POULTRY, THAT IS TO SAY, FOWLS OF THE SPECIES Gallus domesticus , DUCKS, GEESE, TURKEYS AND GUINEA FOWLS": "0105",
          "OTHER LIVE ANIMALS": "0106"
        },
          "0101": {
            "sub_headings": {
              "0101.21.00": "Pure-bred breeding animals",
              "0101.29.00": "Other",
              "0101.30.00": "Asses",
              "0101.90.00": "Other"
            }
          },
          "0102": {
            "sub_headings": {
              "0102.21.00": "Pure-bred breeding animals",
              "0102.29.00": "Other",
              "0102.31.00": "Pure-bred breeding animals",
              "0102.39.00": "Other",
              "0102.90.00": "Other"
            }
          },
          "0103": {
            "sub_headings": {
              "0103.10.00": "Pure-bred breeding animals",
              "0103.91.00": "Weighing less than 50 kg",
              "0103.92.00": "Weighing 50 kg or more"
            }
          },
          "0104": {
            "sub_headings": {
              "0104.10.00": "Sheep",
              "0104.20.00": "Goats"
            }
          },
          "0105": {
            "sub_headings": {
              "0105.11.00": "Fowls of the species Gallus domesticus",
              "0105.12.00": "Turkeys",
              "0105.13.00": "Ducks",
              "0105.14.00": "Geese",
              "0105.15.00": "Guinea fowls",
              "0105.94.00": "Fowls of the species Gallus domesticus",
              "0105.99.00": "Other"
            }
          },
          "0106": {
            "sub_headings": {
              "0106.11.00": "Primates",
              "0106.12.00": "Whales, dolphins and porpoises (mammals of the order Cetacea ); manatees and dugongs (mammals of the order Sirenia ); seals, sea lions and walruses (mammals of the suborder Pinnipedia )",
              "0106.13.00": "Camels and other camelids ( Camelidae )",
              "0106.14.00": "Rabbits and hares",
              "0106.19.00": "Other",
              "0106.20.00": "Reptiles (including snakes and turtles)",
              "0106.31.00": "Birds of prey",
              "0106.32.00": "Psittaciformes (including parrots, parakeets, macaws and cockatoos)",
              "0106.33.00": "Ostriches; emus ( Dromaius novaehollandiae )",
              "0106.39.00": "Other",
              "0106.41.00": "Bees",
              "0106.49.00": "Other",
              "0106.90.00": "Other"
            }
          }
        
      },
      "2": {
        "headings": {
          "MEAT OF BOVINE ANIMALS, FRESH OR CHILLED": "0201",
          "MEAT OF BOVINE ANIMALS, FROZEN": "0202",
          "MEAT OF SWINE, FRESH, CHILLED OR FROZEN": "0203",
          "MEAT OF SHEEP OR GOATS, FRESH, CHILLED OR FROZEN": "0204",
          "EDIBLE OFFAL OF BOVINE ANIMALS, SWINE, SHEEP, GOATS, HORSES, ASSES, MULES OR HINNIES, FRESH, CHILLED OR FROZEN": "0206",
          "MEAT AND EDIBLE OFFAL, OF THE POULTRY OF 0105, FRESH, CHILLED OR FROZEN": "0207",
          "OTHER MEAT AND EDIBLE MEAT OFFAL, FRESH, CHILLED OR FROZEN": "0208",
          "PIG FAT, FREE OF LEAN MEAT, AND POULTRY FAT, NOT RENDERED OR OTHERWISE EXTRACTED, FRESH, CHILLED, FROZEN, SALTED, IN BRINE, DRIED OR SMOKED": "0209",
          "MEAT AND EDIBLE MEAT OFFAL, SALTED, IN BRINE, DRIED OR SMOKED; EDIBLE FLOURS AND MEALS OF MEAT OR MEAT OFFAL": "0210"
        },
          "0201": {
            "sub_headings": {
              "0201.10.00": "Carcasses and half-carcasses",
              "0201.20.00": "Other cuts with bone in",
              "0201.30.00": "Boneless"
            }
          },
          "0202": {
            "sub_headings": {
              "0202.10.00": "Carcasses and half-carcasses",
              "0202.20.00": "Other cuts with bone in",
              "0202.30.00": "Boneless"
            }
          },
          "0203": {
            "sub_headings": {
              "0203.11.00": "Carcasses and half-carcasses",
              "0203.12.00": "Hams, shoulders and cuts thereof, with bone in",
              "0203.19.00": "Other",
              "0203.21.00": "Carcasses and half-carcasses",
              "0203.22.00": "Hams, shoulders and cuts thereof, with bone in",
              "0203.29.00": "Other"
            }
          },
          "0204": {
            "sub_headings": {
              "0204.10.00": "Carcasses and half-carcasses of lamb, fresh or chilled",
              "0204.21.00": "Carcasses and half-carcasses",
              "0204.22.00": "Other cuts with bone in",
              "0204.23.00": "Boneless",
              "0204.30.00": "Carcasses and half-carcasses of lamb, frozen",
              "0204.41.00": "Carcasses and half-carcasses",
              "0204.42.00": "Other cuts with bone in",
              "0204.43.00": "Boneless",
              "0204.50.00": "Meat of goats"
            }
          },
          "0206": {
            "sub_headings": {
              "0206.10.00": "Of bovine animals, fresh or chilled",
              "0206.21.00": "Tongues",
              "0206.22.00": "Livers",
              "0206.29.00": "Other",
              "0206.30.00": "Of swine, fresh or chilled",
              "0206.41.00": "Livers",
              "0206.49.00": "Other",
              "0206.80.00": "Other, fresh or chilled",
              "0206.90.00": "Other, frozen"
            }
          },
          "0207": {
            "sub_headings": {
              "0207.11.00": "Not cut in pieces, fresh or chilled",
              "0207.12.00": "Not cut in pieces, frozen",
              "0207.13.00": "Cuts and offal, fresh or chilled",
              "0207.14.00": "Cuts and offal, frozen",
              "0207.24.00": "Not cut in pieces, fresh or chilled",
              "0207.25.00": "Not cut in pieces, frozen",
              "0207.26.00": "Cuts and offal, fresh or chilled",
              "0207.27.00": "Cuts and offal, frozen",
              "0207.41.00": "Not cut in pieces, fresh or chilled",
              "0207.42.00": "Not cut in pieces, frozen",
              "0207.43.00": "Fatty livers, fresh or chilled",
              "0207.44.00": "Other, fresh or chilled",
              "0207.45.00": "Other, frozen",
              "0207.51.00": "Not cut in pieces, fresh or chilled",
              "0207.52.00": "Not cut in pieces, frozen",
              "0207.53.00": "Fatty livers, fresh or chilled",
              "0207.54.00": "Other, fresh or chilled",
              "0207.55.00": "Other, frozen",
              "0207.60.00": "Of guinea fowls"
            }
          },
          "0208": {
            "sub_headings": {
              "0208.10.00": "Of rabbits or hares",
              "0208.30.00": "Of primates",
              "0208.40.00": "Of whales, dolphins and porpoises (mammals of the order Cetacea ); of manatees and dugongs (mammals of the order Sirenia ); of seals, sea lions and walruses (mammals of the suborder Pinnipedia )",
              "0208.50.00": "Of reptiles (including snakes and turtles)",
              "0208.60.00": "Of camels and other camelids ( Camelidae )",
              "0208.90.00": "Other"
            }
          },
          "0209": {
            "sub_headings": {
              "0209.10.00": "Of pigs",
              "0209.90.00": "Other"
            }
          },
          "0210": {
            "sub_headings": {
              "0210.11.00": "Hams, shoulders and cuts thereof, with bone in",
              "0210.12.00": "Bellies (streaky) and cuts thereof",
              "0210.19.00": "Other",
              "0210.20.00": "Meat of bovine animals",
              "0210.91.00": "Of primates",
              "0210.92.00": "Of whales, dolphins and porpoises (mammals of the order Cetacea ); of manatees and dugongs (mammals of the order Sirenia ); of seals, sea lions and walruses (mammals of the suborder Pinnipedia )",
              "0210.93.00": "Of reptiles (including snakes and turtles)",
              "0210.99.00": "Other"
            }
          }
        
      },
      "3": {
        "headings": {
          "LIVE FISH": "0301",
          "FISH, FRESH OR CHILLED, EXCLUDING FISH FILLETS AND OTHER FISH MEAT OF 0304": "0302",
          "FISH, FROZEN, EXCLUDING FISH FILLETS AND OTHER FISH MEAT OF 0304": "0303",
          "FISH FILLETS AND OTHER FISH MEAT (WHETHER OR NOT MINCED), FRESH, CHILLED OR FROZEN": "0304",
          "FISH, DRIED, SALTED OR IN BRINE; SMOKED FISH, WHETHER OR NOT COOKED BEFORE OR DURING THE SMOKING PROCESS": "0305",
          "CRUSTACEANS, WHETHER IN SHELL OR NOT, LIVE, FRESH, CHILLED, FROZEN, DRIED, SALTED OR IN BRINE; SMOKED CRUSTACEANS, WHETHER IN SHELL OR NOT, WHETHER OR NOT COOKED BEFORE OR DURING THE SMOKING PROCESS; CRUSTACEANS, IN SHELL, COOKED BY STEAMING OR BY BOILING IN WATER, WHETHER OR NOT CHILLED, FROZEN, DRIED, SALTED OR IN BRINE": "0306",
          "MOLLUSCS, WHETHER IN SHELL OR NOT, LIVE, FRESH, CHILLED, FROZEN, DRIED, SALTED OR IN BRINE; SMOKED MOLLUSCS, WHETHER IN SHELL OR NOT, WHETHER OR NOT COOKED BEFORE OR DURING THE SMOKING PROCESS": "0307",
          "AQUATIC INVERTEBRATES OTHER THAN CRUSTACEANS AND MOLLUSCS, LIVE, FRESH, CHILLED, FROZEN, DRIED, SALTED OR IN BRINE; SMOKED AQUATIC INVERTEBRATES OTHER THAN CRUSTACEANS AND MOLLUSCS, WHETHER OR NOT COOKED BEFORE OR DURING THE SMOKING PROCESS": "0308",
          "FLOURS, MEALS AND PELLETS OF FISH, CRUSTACEANS, MOLLUSCS AND OTHER AQUATIC INVERTEBRATES, FIT FOR HUMAN CONSUMPTION": "0309"
        },
        
          "0301": {
            "sub_headings": {
              "0301.11.00": "Freshwater",
              "0301.19.00": "Other",
              "0301.91.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0301.92.00": "Eels ( Anguilla spp. )",
              "0301.93.00": "Carp ( Cyprinus spp., Carassius spp., Ctenopharyngodon idellus, Hypophthalmichthys spp., Cirrhinus spp., Mylopharyngodon piceus, Catla catla, Labeo spp., Osteochilus hasselti, Leptobarbus hoeveni, Megalobrama spp. )",
              "0301.94.00": "Atlantic and Pacific bluefin tunas ( Thunnus thynnus, Thunnus orientalis )",
              "0301.95.00": "Southern bluefin tunas ( Thunnus maccoyii )",
              "0301.99.00": "Other"
            }
          },
          "0302": {
            "sub_headings": {
              "0302.11.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0302.13.00": "Pacific salmon ( Oncorhynchus nerka, Oncorhynchus gorbuscha, Oncorhynchus keta, Oncorhynchus tschawytscha, Oncorhynchus kisutch, Oncorhynchus masou and Oncorhynchus rhodurus )",
              "0302.14.00": "Atlantic salmon ( Salmo salar ) and Danube salmon ( Hucho hucho )",
              "0302.19.00": "Other",
              "0302.21.00": "Halibut ( Reinhardtius hippoglossoides, Hippoglossus hippoglossus, Hippoglossus stenolepis )",
              "0302.22.00": "Plaice ( Pleuronectes platessa )",
              "0302.23.00": "Sole ( Solea spp. )",
              "0302.24.00": "Turbots ( Psetta maxima )",
              "0302.29.00": "Other",
              "0302.31.00": "Albacore or longfinned tunas ( Thunnus alalunga )",
              "0302.32.00": "Yellowfin tunas ( Thunnus albacares )",
              "0302.33.00": "Skipjack tuna (stripe-bellied bonito) (Katsuwonus pelamis)",
              "0302.34.00": "Bigeye tunas ( Thunnus obesus )",
              "0302.35.00": "Atlantic and Pacific bluefin tunas ( Thunnus thynnus, Thunnus orientalis )",
              "0302.36.00": "Southern bluefin tunas ( Thunnus maccoyii )",
              "0302.39.00": "Other",
              "0302.41.00": "Herrings ( Clupea harengus, Clupea pallasii )",
              "0302.42.00": "Anchovies ( Engraulis spp. )",
              "0302.43.00": "Sardines ( Sardina pilchardus, Sardinops spp. ), sardinella ( Sardinella spp. ), brisling or sprats ( Sprattus sprattus )",
              "0302.44.00": "Mackerel ( Scomber scombrus, Scomber australasicus, Scomber japonicus )",
              "0302.45.00": "Jack and horse mackerel ( Trachurus spp. )",
              "0302.46.00": "Cobia ( Rachycentron canadum )",
              "0302.47.00": "Swordfish (Xiphias gladius )",
              "0302.49.00": "Other",
              "0302.51.00": "Cod ( Gadus morhua, Gadus ogac, Gadus macrocephalus )",
              "0302.52.00": "Haddock ( Melanogrammus aeglefinus )",
              "0302.53.00": "Coalfish ( Pollachius virens )",
              "0302.54.00": "Hake ( Merluccius spp., Urophycis spp. )",
              "0302.55.00": "Alaska Pollock ( Theragra chalcogramma )",
              "0302.56.00": "Blue whitings ( Micromesistius poutassou, Micromesistius australis )",
              "0302.59.00": "Other",
              "0302.71.00": "Tilapias ( Oreochromis spp. )",
              "0302.72.00": "Catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. )",
              "0302.73.00": "Carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp. )",
              "0302.74.00": "Eels ( Anguilla spp. )",
              "0302.79.00": "Other",
              "0302.81.00": "Dogfish and other sharks",
              "0302.82.00": "Rays and skates ( Rajidae )",
              "0302.83.00": "Toothfish ( Dissostichus spp. )",
              "0302.84.00": "Seabass ( Dicentrachus spp. )",
              "0302.85.00": "Seabream ( Sparidae )",
              "0302.89.00": "Other",
              "0302.91.00": "Livers, roes and milt",
              "0302.92.00": "Shark fins",
              "0302.99.00": "Other"
            }
          },
          "0303": {
            "sub_headings": {
              "0303.11.00": "Sockeye salmon (red salmon) ( Oncorhynchus nerka )",
              "0303.12.00": "Other Pacific salmon ( Oncorhynchus gorbuscha, Oncorhynchus keta, Oncorhynchus tschawytscha, Oncorhynchus kisutch, Oncorhynchus masou and Oncorhynchus rhodurus )",
              "0303.13.00": "Atlantic salmon ( Salmo salar ) and Danube salmon ( Hucho hucho )",
              "0303.14.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0303.19.00": "Other",
              "0303.23.00": "Tilapias ( Oreochromis spp. )",
              "0303.24.00": "Catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. )",
              "0303.25.00": "Carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp , Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp .)",
              "0303.26.00": "Eels ( Anguilla spp. )",
              "0303.29.00": "Other",
              "0303.31.00": "Halibut ( Reinhardtius hippoglossoides, Hippoglossus hippoglossus, Hippoglossus stenolepis )",
              "0303.32.00": "Plaice ( Pleuronectes platessa )",
              "0303.33.00": "Sole ( Solea spp. )",
              "0303.34.00": "Turbots ( Psetta maxima )",
              "0303.39.00": "Other",
              "0303.41.00": "Albacore or longfinned tunas ( Thunnus alalunga )",
              "0303.42.00": "Yellowfin tunas ( Thunnus albacares )",
              "0303.43.00": "Skipjack tuna (stripe-bellied bonito) (Katsuwonus pelamis)",
              "0303.44.00": "Bigeye tunas ( Thunnus obesus )",
              "0303.45.00": "Atlantic and Pacific bluefin tunas ( Thunnus thynnus, Thunnus orientalis )",
              "0303.46.00": "Southern bluefin tunas ( Thunnus maccoyii )",
              "0303.49.00": "Other",
              "0303.51.00": "Herrings ( Clupea harengus, Clupea pallasii )",
              "0303.53.00": "Sardines ( Sardina pilchardus, Sardinops spp. ), sardinella ( Sardinella spp. ), brisling or sprats ( Sprattus sprattus )",
              "0303.54.00": "Mackerel (Scomber scombrus, Scomber australasicus, Scomber japonicus )",
              "0303.55.00": "Jack and horse mackerel ( Trachurus spp. )",
              "0303.56.00": "Cobia ( Rachycentron canadum )",
              "0303.57.00": "Swordfish ( Xiphias gladius )",
              "0303.59.00": "Other",
              "0303.63.00": "Cod ( Gadus morhua, Gadus ogac, Gadus macrocephalus )",
              "0303.64.00": "Haddock ( Melanogrammus aeglefinus )",
              "0303.65.00": "Coalfish ( Pollachius virens )",
              "0303.66.00": "Hake ( Merluccius spp., Urophycis spp. )",
              "0303.67.00": "Alaska Pollock ( Theragra chalcogramma )",
              "0303.68.00": "Blue whitings ( Micromesistius poutassou, Micromesistius australis )",
              "0303.69.00": "Other",
              "0303.81.00": "Dogfish and other sharks",
              "0303.82.00": "Rays and skates ( Rajidae )",
              "0303.83.00": "Toothfish ( Dissostichus spp. )",
              "0303.84.00": "Seabass ( Dicentrachus spp. )",
              "0303.89.00": "Other",
              "0303.91.00": "Livers, roes and milt",
              "0303.92.00": "Shark fins",
              "0303.99.00": "Other"
            }
          },
          "0304": {
            "sub_headings": {
              "0304.31.00": "Tilapias ( Oreochromis spp. )",
              "0304.32.00": "Catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. )",
              "0304.33.00": "Nile perch ( Lates niloticus )",
              "0304.39.00": "Other",
              "0304.41.00": "Pacific salmon ( Oncorhynchus nerka, Oncorhynchus gorbuscha, Oncorhynchus keta, Oncorhynchus tschawytscha, Oncorhynchus kisutch, Oncorhynchus masou and Oncorhynchus rhodurus ), Atlantic salmon ( Salmo salar ) and Danube salmon ( Hucho hucho )",
              "0304.42.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0304.43.00": "Flat fish ( Pleuronectidae, Bothidae, Cynoglossidae, Soleidae, Scophthalmidae and Citharidae )",
              "0304.44.00": "Fish of the families Bregmacerotidae, Euclichthyidae, Gadidae, Macrouridae, Melanonidae, Merlucciidae, Moridae and Muraenolepididae",
              "0304.45.00": "Swordfish ( Xiphias gladius )",
              "0304.46.00": "Toothfish ( Dissostichus spp. )",
              "0304.47.00": "Dogfish and other sharks",
              "0304.48.00": "Rays and skates (Rajidae)",
              "0304.49.00": "Other",
              "0304.51.00": "Tilapias ( Oreochromis spp .), catfish ( Pangasius spp ., Silurus spp ., Clarias spp ., Ictalurus spp .), carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp .), eels ( Anguilla spp .), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp .)",
              "0304.52.00": "Salmonidae",
              "0304.53.00": "Fish of the families Bregmacerotidae, Euclichthyidae, Gadidae, Macrouridae, Melanonidae, Merlucciidae, Moridae and Muraenolepididae",
              "0304.54.00": "Swordfish ( Xiphias gladius )",
              "0304.55.00": "Toothfish ( Dissostichus spp. )",
              "0304.56.00": "Dogfish and other sharks",
              "0304.57.00": "Rays and skates ( Rajidae)",
              "0304.59.00": "Other",
              "0304.61.00": "Tilapias ( Oreochromis spp. )",
              "0304.62.00": "Catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. )",
              "0304.63.00": "Nile perch ( Lates niloticus )",
              "0304.69.00": "Other",
              "0304.71.00": "Cod ( Gadus morhua, Gadus ogac, Gadus macrocephalus )",
              "0304.72.00": "Haddock ( Melanogrammus aeglefinus )",
              "0304.73.00": "Coalfish ( Pollachius virens )",
              "0304.74.00": "Hake ( Merluccius spp., Urophycis spp. )",
              "0304.75.00": "Alaska Pollock ( Theragra chalcogramma )",
              "0304.79.00": "Other",
              "0304.81.00": "Pacific salmon ( Oncorhynchus nerka, Oncorhynchus gorbuscha, Oncorhynchus keta, Oncorhynchus tschawytscha, Oncorhynchus kisutch, Oncorhynchus masou and Oncorhynchus rhodurus ), Atlantic salmon ( Salmo salar ) and Danube salmon ( Hucho hucho )",
              "0304.82.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0304.83.00": "Flat fish ( Pleuronectidae, Bothidae, Cynoglossidae, Soleidae, Scophthalmidae and Citharidae )",
              "0304.84.00": "Swordfish ( Xiphias gladius )",
              "0304.85.00": "Toothfish ( Dissostichus spp. )",
              "0304.86.00": "Herrings ( Clupea harengus, Clupea pallasii )",
              "0304.87.00": "Tunas ( of the genus Thunnus ), skipjack tuna (stripe-bellied bonito) (Katsuwonus pelamis )",
              "0304.88.00": "Dogfish, other sharks, rays and skates ( Rajidae )",
              "0304.89.00": "Other",
              "0304.91.00": "Swordfish ( Xiphias gladius )",
              "0304.92.00": "Toothfish ( Dissostichus spp. )",
              "0304.93.00": "Tilapias ( Oreochromis spp. ), catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. ), carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp . ), eels ( Anguilla spp. ), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp. )",
              "0304.94.00": "Alaska Pollock ( Theragra chalcogramma )",
              "0304.95.00": "Fish of the families Bregmacerotidae, Euclichthyidae, Gadidae, Macrouridae, Melanonidae, Merlucciidae, Moridae and Muraenolepididae other than Alaska Pollock ( Theragra chalcogramma )",
              "0304.96.00": "Dogfish and other sharks",
              "0304.97.00": "Rays and skates ( Rajidae )",
              "0304.99.00": "Other"
            }
          },
          "0305": {
            "sub_headings": {
              "0305.20.00": "Livers, roes and milt of fish, dried, smoked, salted or in brine",
              "0305.31.00": "Tilapias ( Oreochromis spp. ), catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. ), carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp . ), eels ( Anguilla spp. ), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp. )",
              "0305.32.00": "Fish of the families Bregmacerotidae, Euclichthyidae, Gadidae, Macrouridae, Melanonidae, Merlucciidae, Moridae and Muraenolepididae",
              "0305.39.00": "Other",
              "0305.41.00": "Pacific salmon ( Oncorhynchus nerka, Oncorhynchus gorbuscha, Oncorhynchus keta, Oncorhynchus tschawytscha, Oncorhynchus kisutch, Oncorhynchus masou and Oncorhynchus rhodurus ), Atlantic salmon ( Salmo salar ) and Danube salmon ( Hucho hucho )",
              "0305.42.00": "Herrings ( Clupea harengus, Clupea pallasii )",
              "0305.43.00": "Trout ( Salmo trutta, Oncorhynchus mykiss, Oncorhynchus clarki, Oncorhynchus aguabonita, Oncorhynchus gilae, Oncorhynchus apache and Oncorhynchus chrysogaster )",
              "0305.44.00": "Tilapias ( Oreochromis spp. ), catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. ), carp ( Cyprinus spp ., Carassius spp ., Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp ., Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp . ), Eels ( Anguilla spp. ), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp. )",
              "0305.49.00": "Other",
              "0305.51.00": "Cod ( Gadus morhua, Gadus ogac, Gadus macrocephalus )",
              "0305.52.00": "Tilapias ( Oreochromis spp .), catfish ( Pangasius spp ., Silurus spp ., Clarias spp ., Ictalurus spp .), carp ( Cyprinus spp . , Carassius spp . , Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp . , Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp . ), eels ( Anguilla spp .), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp . )",
              "0305.53.00": "Fish of the families Bregmacerotidae , Euclichthyidae , Gadidae , Macrouridae , Melanonidae , Merlucciidae , Moridae and Muraenolepididae , other than cod ( Gadus morhua , Gadus ogac , Gadus macrocephalus )",
              "0305.54.00": "Herrings ( Clupea harengus , Clupea pallasii ), anchovies ( Engraulis spp . ), sardines ( Sardina pilchardus , Sardinops spp . ), sardinella ( Sardinella spp . ), brisling or sprats ( Sprattus sprattus ), mackerel ( Scomber scombrus , Scomber australasicus , Scomber japonicus ), Indian mackerels ( Rastrelliger spp . ), seerfishes ( Scomberomorus spp . ), jack and horse mackerel ( Trachurus spp . ), jacks, crevalles ( Caranx spp . ), cobia ( Rachycentron canadum ), silver pomfrets ( Pampus spp . ), Pacific saury ( Cololabis saira ), scads ( Decapterus spp. ), capelin ( Mallotus villosus ), swordfish ( Xiphias gladius ), Kawakawa ( Euthynnus affinis ), bonitos ( Sarda spp . ), marlins, sailfishes, spearfish ( Istiophoridae )",
              "0305.59.00": "Other",
              "0305.61.00": "Herrings ( Clupea harengus, Clupea pallasii )",
              "0305.62.00": "Cod ( Gadus morhua, Gadus ogac, Gadus macrocephalus )",
              "0305.63.00": "Anchovies ( Engraulis spp. )",
              "0305.64.00": "Tilapias ( Oreochromis spp. ), catfish ( Pangasius spp., Silurus spp., Clarias spp., Ictalurus spp. ), carp ( Cyprinus spp . , Carassius spp . , Ctenopharyngodon idellus , Hypophthalmichthys spp ., Cirrhinus spp ., Mylopharyngodon piceus , Catla catla , Labeo spp . , Osteochilus hasselti , Leptobarbus hoeveni , Megalobrama spp . ), eels ( Anguilla spp. ), Nile perch ( Lates niloticus ) and snakeheads ( Channa spp. )",
              "0305.69.00": "Other",
              "0305.71.00": "Shark fins",
              "0305.72.00": "Fish heads, tails and maws",
              "0305.79.00": "Other"
            }
          },
          "0306": {
            "sub_headings": {
              "0306.11.00": "Rock lobster and other sea crawfish ( Palinurus spp., Panulirus spp., Jasus spp. )",
              "0306.12.00": "Lobsters ( Homarus spp. )",
              "0306.14.00": "Crabs",
              "0306.15.00": "Norway lobsters ( Nephrops norvegicus )",
              "0306.16.00": "Cold-water shrimps and prawns ( Pandalus spp., Crangon crangon )",
              "0306.17.00": "Other shrimps and prawns",
              "0306.19.00": "Other",
              "0306.31.00": "Rock lobster and other sea crawfish ( Palinurus spp., Panulirus spp., Jasus spp .)",
              "0306.32.00": "Lobsters ( Homarus spp. )",
              "0306.33.00": "Crabs",
              "0306.34.00": "Norway lobsters ( Nephrops norvegicus )",
              "0306.35.00": "Cold-water shrimps and prawns ( Pandalus spp., Crangon crangon )",
              "0306.36.00": "Other shrimps and prawns",
              "0306.39.00": "Other",
              "0306.91.00": "Rock lobster and other sea crawfish ( Palinurus spp., Panulirus spp., Jasus spp .)",
              "0306.92.00": "Lobsters ( Homarus spp. )",
              "0306.93.00": "Crabs",
              "0306.94.00": "Norway lobsters ( Nephrops norvegicus )",
              "0306.95.00": "Shrimps and prawns",
              "0306.99.00": "Other"
            }
          },
          "0307": {
            "sub_headings": {
              "0307.11.00": "Live, fresh or chilled",
              "0307.12.00": "Frozen",
              "0307.19.00": "Other",
              "0307.21.00": "Live, fresh or chilled",
              "0307.22.00": "Frozen",
              "0307.29.00": "Other",
              "0307.31.00": "Live, fresh or chilled",
              "0307.32.00": "Frozen",
              "0307.39.00": "Other",
              "0307.42.00": "Live, fresh or chilled",
              "0307.43.00": "Frozen",
              "0307.49.00": "Other",
              "0307.51.00": "Live, fresh or chilled",
              "0307.52.00": "Frozen",
              "0307.59.00": "Other",
              "0307.60.00": "Snails, other than sea snails",
              "0307.71.00": "Live, fresh or chilled",
              "0307.72.00": "Frozen",
              "0307.79.00": "Other",
              "0307.81.00": "Live, fresh or chilled abalone ( Haliotis spp .)",
              "0307.82.00": "Live, fresh or chilled stromboid conchs ( Strombus spp .)",
              "0307.83.00": "Frozen abalone ( Haliotis spp .)",
              "0307.84.00": "Frozen stromboid conchs ( Strombus spp .)",
              "0307.87.00": "Other abalone ( Haliotis spp .)",
              "0307.88.00": "Other stromboid conchs ( Strombus spp .)",
              "0307.91.00": "Live, fresh or chilled",
              "0307.92.00": "Frozen",
              "0307.99.00": "Other"
            }
          },
          "0308": {
            "sub_headings": {
              "0308.11.00": "Live, fresh or chilled",
              "0308.12.00": "Frozen",
              "0308.19.00": "Other",
              "0308.21.00": "Live, fresh or chilled",
              "0308.22.00": "Frozen",
              "0308.29.00": "Other",
              "0308.30.00": "Jellyfish ( Rhopilema spp. )",
              "0308.90.00": "Other"
            }
          },
          "0309": {
            "sub_headings": {
              "0309.10.00": "Of fish",
              "0309.90.00": "Other"
            }
          }
        
      },
      "4": {
        "headings": {
          "MILK AND CREAM, NOT CONCENTRATED NOR CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER": "0401",
          "MILK AND CREAM, CONCENTRATED OR CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER": "0402",
          "YOGURT; BUTTERMILK, CURDLED MILK AND CREAM, KEPHIR AND OTHER FERMENTED OR ACIDIFIED MILK AND CREAM, WHETHER OR NOT CONCENTRATED OR CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER OR FLAVOURED OR CONTAINING ADDED FRUIT, NUTS OR COCOA": "0403",
          "WHEY, WHETHER OR NOT CONCENTRATED OR CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER; PRODUCTS CONSISTING OF NATURAL MILK CONSTITUENTS, WHETHER OR NOT CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER, NOT ELSEWHERE SPECIFIED OR INCLUDED": "0404",
          "BUTTER AND OTHER FATS AND OILS DERIVED FROM MILK; DAIRY SPREADS": "0405",
          "CHEESE AND CURD": "0406",
          "BIRDS' EGGS, IN SHELL, FRESH, PRESERVED OR COOKED": "0407",
          "BIRDS' EGGS, NOT IN SHELL, AND EGG YOLKS, FRESH, DRIED, COOKED BY STEAMING OR BY BOILING IN WATER, MOULDED, FROZEN OR OTHERWISE PRESERVED, WHETHER OR NOT CONTAINING ADDED SUGAR OR OTHER SWEETENING MATTER": "0408",
          "INSECTS AND OTHER EDIBLE PRODUCTS OF ANIMAL ORIGIN, NOT ELSEWHERE SPECIFIED OR INCLUDED": "0410"
        },
        
          "0401": {
            "sub_headings": {
              "0401.10.00": "Of a fat content, by weight, not exceeding 1%",
              "0401.20.00": "Of a fat content, by weight, exceeding 1% but not exceeding 6%",
              "0401.40.00": "Of a fat content, by weight, exceeding 6% but not exceeding 10%",
              "0401.50.00": "Of a fat content, by weight, exceeding 10%"
            }
          },
          "0402": {
            "sub_headings": {
              "0402.10.00": "In powder, granules or other solid forms, of a fat content, by weight, not exceeding 1.5%",
              "0402.21.00": "Not containing added sugar or other sweetening matter",
              "0402.29.00": "Other",
              "0402.91.00": "Not containing added sugar or other sweetening matter",
              "0402.99.00": "Other"
            }
          },
          "0403": {
            "sub_headings": {
              "0403.20.10": "Containing chocolate, spices, coffee or coffee extracts, plants, parts of plants, cereals or bakers’ wares",
              "0403.20.90": "Other",
              "0403.90.00": "Other"
            }
          },
          "0404": {
            "sub_headings": {
              "0404.10.00": "Whey and modified whey, whether or not concentrated or containing added sugar or other sweetening matter",
              "0404.90.00": "Other"
            }
          },
          "0405": {
            "sub_headings": {
              "0405.10.00": "Butter",
              "0405.20.00": "Dairy spreads",
              "0405.90.00": "Other"
            }
          },
          "0406": {
            "sub_headings": {
              "0406.10.00": "Fresh (unripened or uncured) cheese, including whey cheese, and curd",
              "0406.20.00": "Grated or powdered cheese, of all kinds",
              "0406.30.00": "Processed cheese, not grated or powdered",
              "0406.40.10": "Cheese, of the following types: (a) roquefort; (b) stilton",
              "0406.40.90": "Other",
              "0406.90.10": "Cheese, of the following types: (a) made wholly from goats' milk, other than fetta or kasseri; (b) surface-ripened soft, having: (i) a fat content in the dry matter of not less than 50% by weight; and (ii) a moisture content of not less than 65% by weight of the non-fatty matter",
              "0406.90.90": "Other"
            }
          },
          "0407": {
            "sub_headings": {
              "0407.11.00": "Of fowls of the specises Gallus domesticus",
              "0407.19.00": "Other",
              "0407.21.00": "Of fowls of the specises Gallus domesticus",
              "0407.29.00": "Other",
              "0407.90.00": "Other"
            }
          },
          "0408": {
            "sub_headings": {
              "0408.11.00": "Dried",
              "0408.19.00": "Other",
              "0408.91.00": "Dried",
              "0408.99.00": "Other"
            }
          },
          "0410": {
            "sub_headings": {
              "0410.10.00": "Insects",
              "0410.90.00": "Other"
            }
          }
        
      },
      "5": {
        "headings": {
          "PIGS', HOGS' OR BOARS' BRISTLES AND HAIR; BADGER HAIR AND OTHER BRUSH MAKING HAIR; WASTE OF SUCH BRISTLES OR HAIR": "0502",
          "SKINS AND OTHER PARTS OF BIRDS, WITH THEIR FEATHERS OR DOWN, FEATHERS AND PARTS OF FEATHERS (WHETHER OR NOT WITH TRIMMED EDGES) AND DOWN, NOT FURTHER WORKED THAN CLEANED, DISINFECTED OR TREATED FOR PRESERVATION; POWDER AND WASTE OF FEATHERS OR PARTS OF FEATHERS": "0505",
          "BONES AND HORN-CORES, UNWORKED, DEFATTED, SIMPLY PREPARED (BUT NOT CUT TO SHAPE), TREATED WITH ACID OR DEGELATINISED; POWDER AND WASTE OF THESE PRODUCTS": "0506",
          "IVORY, TORTOISE-SHELL, WHALEBONE AND WHALEBONE HAIR, HORNS, ANTLERS, HOOVES, NAILS, CLAWS AND BEAKS, UNWORKED OR SIMPLY PREPARED BUT NOT CUT TO SHAPE; POWDER AND WASTE OF THESE PRODUCTS": "0507",
          "ANIMAL PRODUCTS NOT ELSEWHERE SPECIFIED OR INCLUDED; DEAD ANIMALS OF CHAPTER 1 OR 3, UNFIT FOR HUMAN CONSUMPTION": "0511"
        },
        
          "0502": {
            "sub_headings": {
              "0502.10.00": "Pigs', hogs' or boars' bristles and hair and waste thereof",
              "0502.90.00": "Other",
              "0504.00.00": "GUTS, BLADDERS AND STOMACHS OF ANIMALS (OTHER THAN FISH), WHOLE AND PIECES THEREOF, FRESH, CHILLED, FROZEN, SALTED, IN BRINE, DRIED OR SMOKED"
            }
          },
          "0505": {
            "sub_headings": {
              "0505.10.00": "Feathers of a kind used for stuffing; down",
              "0505.90.00": "Other"
            }
          },
          "0506": {
            "sub_headings": {
              "0506.10.00": "Ossein and bones treated with acid",
              "0506.90.00": "Other"
            }
          },
          "0507": {
            "sub_headings": {
              "0507.10.00": "Ivory; ivory powder and waste",
              "0507.90.00": "Other"
            }
          },
          "0511": {
            "sub_headings": {
              "0511.10.00": "Bovine semen",
              "0511.91.00": "Products of fish or crustaceans, molluscs or other aquatic invertebrates; dead animals of Chapter 3",
              "0511.99.10": "Horsehair and horsehair waste, whether or not put up as a layer with or without supporting material",
              "0511.99.90": "Other"
            }
          }
        
      }
    
  }
}
# Request/Response models
class ClassificationRequest(BaseModel):
    text: str
    level: ClassificationLevel
    parent_path: Optional[List[str]] = None  # Path to parent classifications

class SingleLevelResponse(BaseModel):
    predicted_label: str
    label_code: str
    confidence_score: float
    all_scores: Dict[str, float]
    level: ClassificationLevel

class HierarchicalClassificationRequest(BaseModel):
    text: str
    max_depth: Optional[int] = None  # Maximum depth to classify (1=sections only, 4=all levels)

class HierarchicalClassificationResponse(BaseModel):
    text: str
    classification_path: List[SingleLevelResponse]
    full_code: str  # Complete hierarchical code
    processing_time_ms: float

class MultiLevelClassifier:
    def __init__(self):
        self.level_classifiers: Dict[str, 'LevelClassifier'] = {}
        # Initialize base sections classifier
        self.level_classifiers['sections'] = LevelClassifier('sections', SECTION_MAP)
    
    def _get_available_labels(self, level: ClassificationLevel, parent_path: List[str]) -> Dict[str, str]:
        """Get available labels for a given level based on parent path"""
        if level == ClassificationLevel.SECTIONS:
            return SECTION_MAP
        
        if not parent_path:
            return {}
        
        # Navigate through the hierarchy
        current_mapping = HIERARCHICAL_MAPPINGS
        
        try:
            if level == ClassificationLevel.CHAPTERS:
                section_code = parent_path[0]  # Parent section code
                return current_mapping.get(section_code, {}).get("chapters", {})
            
            elif level == ClassificationLevel.HEADINGS:
                section_code, chapter_code = parent_path[0], parent_path[1]
                section_data = current_mapping.get(section_code, {})
                return section_data.get(chapter_code, {}).get("headings", {})
            
            elif level == ClassificationLevel.SUB_HEADINGS:
                section_code, chapter_code, heading_code = parent_path[0], parent_path[1], parent_path[2]
                section_data = current_mapping.get(section_code, {})
                chapter_data = section_data.get(chapter_code, {})
                return chapter_data.get(heading_code, {}).get("sub_headings", {})
        
        except (IndexError, KeyError):
            return {}
        
        return {}
    
    def _get_classifier_key(self, level: ClassificationLevel, parent_path: List[str]) -> str:
        """Generate a unique key for the classifier based on level and parent path"""
        if level == ClassificationLevel.SECTIONS:
            return "sections"
        
        path_str = "_".join(parent_path) if parent_path else ""
        return f"{level.value}_{path_str}"
    
    async def _get_or_create_classifier(self, level: ClassificationLevel, parent_path: List[str]) -> 'LevelClassifier':
        """Get or create a classifier for the specific level and parent path"""
        classifier_key = self._get_classifier_key(level, parent_path)
        
        if classifier_key not in self.level_classifiers:
            label_mapping = self._get_available_labels(level, parent_path)
            if not label_mapping:
                raise HTTPException(
                    status_code=400,
                    detail=f"No labels available for {level.value} with parent path {parent_path}"
                )
            
            self.level_classifiers[classifier_key] = LevelClassifier(classifier_key, label_mapping)
        
        return self.level_classifiers[classifier_key]
    
    async def initialize_all_embeddings(self):
        """Initialize embeddings for sections classifier"""
        print("Initializing sections classifier...")
        await self.level_classifiers['sections'].initialize_embeddings()
        print("Base sections classifier initialized!")
    
    async def classify_single_level(
        self, 
        text: str, 
        level: ClassificationLevel,
        parent_path: Optional[List[str]] = None
    ) -> SingleLevelResponse:
        """Classify text at a single level given the parent path"""
        parent_path = parent_path or []
        classifier = await self._get_or_create_classifier(level, parent_path)
        
        result = await classifier.classify(text)
        result.level = level
        return result
    
    async def classify_hierarchical(
        self, 
        text: str, 
        max_depth: Optional[int] = None
    ) -> HierarchicalClassificationResponse:
        """Classify text through hierarchical levels until no more levels available"""
        import time
        start_time = time.time()
        
        classification_path = []
        parent_path = []
        full_code_parts = []
        
        levels = [
            ClassificationLevel.SECTIONS,
            ClassificationLevel.CHAPTERS,
            ClassificationLevel.HEADINGS,
            ClassificationLevel.SUB_HEADINGS
        ]
        
        current_depth = 0
        max_depth = max_depth or len(levels)
        
        for level in levels:
            if current_depth >= max_depth:
                break
                
            try:
                # Classify at current level
                result = await self.classify_single_level(text, level, parent_path)
                classification_path.append(result)
                
                # Update parent path with the predicted code
                parent_path.append(result.label_code)
                full_code_parts.append(result.label_code)
                
                current_depth += 1
                
                # Check if next level has available labels
                if current_depth < len(levels):
                    next_level = levels[current_depth]
                    available_labels = self._get_available_labels(next_level, parent_path)
                    if not available_labels:
                        print(f"No labels available for {next_level.value} with path {parent_path}")
                        break
                        
            except HTTPException as e:
                print(f"Stopping classification at {level.value}: {e.detail}")
                break
            except Exception as e:
                print(f"Error at {level.value}: {str(e)}")
                break
        
        processing_time = (time.time() - start_time) * 1000
        full_code = ".".join(full_code_parts)
        
        return HierarchicalClassificationResponse(
            text=text,
            classification_path=classification_path,
            full_code=full_code,
            processing_time_ms=round(processing_time, 2)
        )

class LevelClassifier:
    def __init__(self, classifier_id: str, label_mapping: Dict[str, str]):
        self.classifier_id = classifier_id
        self.embeddings: Optional[Dict[str, np.ndarray]] = None
        self.label_mapping = label_mapping
        self.label_names = list(label_mapping.keys())
        
        # Create classifier-specific directories
        self.cache_dir = os.path.join(EMBEDDINGS_BASE_DIR, classifier_id)
        self.embeddings_file = os.path.join(self.cache_dir, "embeddings.pkl")
        self.hash_file = os.path.join(self.cache_dir, "labels_hash.txt")
        
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_labels_hash(self) -> str:
        """Generate a hash of the label names to detect changes"""
        labels_str = json.dumps(sorted(self.label_names))
        return hashlib.md5(labels_str.encode()).hexdigest()
    
    def _save_embeddings_to_file(self):
        """Save embeddings and labels hash to files"""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            with open(self.hash_file, 'w') as f:
                f.write(self._get_labels_hash())
            
            print(f"  ✓ {self.classifier_id} embeddings saved")
        except Exception as e:
            print(f"  ✗ Warning: Failed to save {self.classifier_id} embeddings: {e}")
    
    def _load_embeddings_from_file(self) -> bool:
        """Load embeddings from file if they exist and are valid"""
        try:
            if not (os.path.exists(self.embeddings_file) and os.path.exists(self.hash_file)):
                return False
            
            with open(self.hash_file, 'r') as f:
                stored_hash = f.read().strip()
            
            current_hash = self._get_labels_hash()
            if stored_hash != current_hash:
                return False
            
            with open(self.embeddings_file, 'rb') as f:
                self.embeddings = pickle.load(f)
            
            if not isinstance(self.embeddings, dict):
                return False
            
            if set(self.embeddings.keys()) != set(self.label_names):
                return False
            
            print(f"  ✓ Loaded cached embeddings for {self.classifier_id}")
            return True
            
        except Exception as e:
            print(f"  ✗ Error loading {self.classifier_id} embeddings: {e}")
            return False
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Ollama API"""
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {
            "model": MODEL_NAME,
            "prompt": text
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=500, 
                            detail=f"Ollama API error: {response.status}"
                        )
                    
                    data = await response.json()
                    embedding = np.array(data["embedding"])
                    return embedding
                    
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to connect to Ollama: {str(e)}"
                )
    
    async def initialize_embeddings(self):
        """Load embeddings from file or generate new ones if needed"""
        if self.embeddings is not None:
            return
        
        if not self.label_names:
            print(f"  ⚠ No labels defined for {self.classifier_id}")
            return
        
        # Try to load from file first
        if self._load_embeddings_from_file():
            return
        
        # Generate new embeddings
        print(f"  → Generating embeddings for {self.classifier_id}...")
        self.embeddings = {}
        
        for i, label_name in enumerate(self.label_names, 1):
            print(f"    Processing {i}/{len(self.label_names)}: {label_name}")
            
            # Create descriptive text for embedding
            descriptive_text = f"{label_name} classification category"
            embedding = await self.get_embedding(descriptive_text)
            self.embeddings[label_name] = embedding
        
        # Save embeddings to file
        self._save_embeddings_to_file()
        print(f"  ✓ {self.classifier_id} embeddings initialized!")
    
    async def classify(self, text: str) -> SingleLevelResponse:
        """Classify input text into one of the labels"""
        await self.initialize_embeddings()
        
        if not self.embeddings:
            raise HTTPException(
                status_code=500, 
                detail=f"No embeddings available for classifier {self.classifier_id}"
            )
        
        # Get embedding for input text
        input_embedding = await self.get_embedding(text)
        
        # Calculate cosine similarities
        similarities = {}
        for label_name, label_embedding in self.embeddings.items():
            input_emb_2d = input_embedding.reshape(1, -1)
            label_emb_2d = label_embedding.reshape(1, -1)
            
            similarity = cosine_similarity(input_emb_2d, label_emb_2d)[0][0]
            similarities[label_name] = float(similarity)
        
        # Find the label with highest similarity
        best_label = max(similarities, key=similarities.get)
        best_score = similarities[best_label]
        
        return SingleLevelResponse(
            predicted_label=best_label,
            label_code=self.label_mapping[best_label],
            confidence_score=best_score,
            all_scores=similarities,
            level=ClassificationLevel.SECTIONS  # Will be overridden by caller
        )

# Initialize multi-level classifier
multi_classifier = MultiLevelClassifier()

# Example usage and testing
if __name__ == "__main__":
    # import uvicorn
    
    # Example test function
    async def test_hierarchical_classifier():
        test_inputs = [
            "Horses",
            "Animal Assess",
            "Fish Seafood",
        ]
        
        print("=== Testing Hierarchical Classification ===\n")
        
        for text in test_inputs:
            try:
                print(f"Input: '{text}'")
                
                # Test hierarchical classification
                result = await multi_classifier.classify_hierarchical(text)
                
                print(f"Full Code: {result.full_code}")
                print("Classification Path:")
                for classification in result.classification_path:
                    print(f"  {classification.level.value}: {classification.predicted_label} ({classification.label_code}) - {classification.confidence_score:.4f}")
                
                print(f"Processing time: {result.processing_time_ms}ms\n")
                
            except Exception as e:
                print(f"Error classifying '{text}': {e}\n")
    
    # Uncomment to run tests
    asyncio.run(test_hierarchical_classifier())
    
    # Run the FastAPI server
    # uvicorn.run(app, host="0.0.0.0", port=8000)