#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Potions Amélioré - Version 2.0
Système complet de création et gestion de potions alchimiques
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
import random
import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import shutil

# ==================== MODELS ====================

@dataclass
class Ingredient:
    """Modèle pour un ingrédient avec types de potions autorisés"""
    id: str
    name: str
    effect: str
    type: str  # "positif" ou "négatif"
    quality: str  # "Mineur", "Majeur", "Légendaire", "Mythique"
    duration: str
    rarity: str = "Commun"
    description: str = ""
    allowed_potion_types: List[str] = None  # Types de potions autorisés
    
    def __post_init__(self):
        if self.allowed_potion_types is None:
            # Par défaut, autorisé dans tous les types
            self.allowed_potion_types = ["Potion", "Poison", "Onguent", "Filtre", "Substrat", "Médicament"]

@dataclass
class Base:
    """Modèle pour une base de potion"""
    id: str
    name: str
    potion_type: str
    description: str = ""
    rarity: str = "Commun"

@dataclass
class Potion:
    """Modèle pour une potion créée"""
    id: str
    name: str
    base: str
    ingredient1: str
    ingredient2: str
    category: str
    created_at: str
    is_favorite: bool = False
    notes: str = ""
    
    def get_key(self) -> str:
        """Clé unique pour identifier les doublons"""
        return f"{self.base}|{min(self.ingredient1, self.ingredient2)}|{max(self.ingredient1, self.ingredient2)}"

# ==================== DATA MANAGER ====================

class DataManager:
    """Gestionnaire de données avec sauvegarde automatique"""
    
    def __init__(self, data_file: str = "data/potions_data.json"):
        self.data_file = Path(data_file)
        self.backup_dir = Path("backups")
        self.data = self._load_data()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Créer les dossiers nécessaires"""
        self.data_file.parent.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        Path("exports").mkdir(exist_ok=True)
    
    def _load_data(self) -> dict:
        """Charger les données depuis le fichier JSON"""
        if not self.data_file.exists():
            return self._create_default_data()
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._migrate_data(data)
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {e}")
            return self._create_default_data()
    
    def _create_default_data(self) -> dict:
        """Créer la structure de données par défaut"""
        return {
            "version": "2.0",
            "metadata": {
                "created": datetime.datetime.now().isoformat(),
                "last_modified": datetime.datetime.now().isoformat(),
                "total_potions": 0,
                "total_ingredients": 0
            },
            "config": {
                "auto_save": True,
                "backup_frequency": 10,
                "theme": "light"
            },
            "bases": {
                "eau": {"id": "eau", "name": "Eau", "potion_type": "Potion", "description": "Base liquide standard"},
                "huile": {"id": "huile", "name": "Huile", "potion_type": "Poison", "description": "Base huileuse toxique"},
                "pate": {"id": "pate", "name": "Pâte", "potion_type": "Onguent", "description": "Base épaisse topique"},
                "vin": {"id": "vin", "name": "Vin alchimique", "potion_type": "Filtre", "description": "Base alcoolisée magique"},
                "cendre": {"id": "cendre", "name": "Cendre", "potion_type": "Substrat", "description": "Base poudreuse rituelle"},
                "quartz": {"id": "quartz", "name": "Poudre de quartz", "potion_type": "Médicament", "description": "Base cristalline curative"}
            },
            "ingredients": {},
            "potions": {},
            "tags": [],
            "favorites": []
        }

    def _migrate_data(self, old_data: dict) -> dict:
        """Migrer l'ancien format vers le nouveau"""
        if "version" in old_data and old_data["version"] == "2.0":
            for ing_id, ing_data in old_data.get("ingredients", {}).items():
                if "allowed_potion_types" not in ing_data:
                    ing_data["allowed_potion_types"] = ["Potion", "Poison", "Onguent", "Filtre", "Substrat", "Médicament"]
                ing_data.pop("contraindications", None)
                ing_data.pop("synergies", None)
            return old_data
        
        new_data = self._create_default_data()
        if "ingredients" in old_data:
            for name, props in old_data["ingredients"].items():
                ingredient_id = name.lower().replace(" ", "_").replace("'", "")
                new_data["ingredients"][ingredient_id] = {
                    "id": ingredient_id,
                    "name": name,
                    "effect": props.get("effet", ""),
                    "type": props.get("type", "positif"),
                    "quality": props.get("qualité", "Mineur"),
                    "duration": props.get("durée", "Instantané"),
                    "rarity": "Commun",
                    "description": "",
                    "allowed_potion_types": ["Potion", "Poison", "Onguent", "Filtre", "Substrat", "Médicament"]
                }
        if "potions_creees" in old_data:
            for i, potion in enumerate(old_data["potions_creees"]):
                potion_id = f"potion_{i+1}"
                new_data["potions"][potion_id] = {
                    "id": potion_id,
                    "name": potion.get("nom", ""),
                    "base": potion.get("base", ""),
                    "ingredient1": potion.get("ingredient1", ""),
                    "ingredient2": potion.get("ingredient2", ""),
                    "category": potion.get("categorie", "Mineur"),
                    "created_at": datetime.datetime.now().isoformat(),
                    "is_favorite": False,
                    "notes": ""
                }
        return new_data

    def save_data(self):
        """Sauvegarder les données"""
        try:
            if self.data_file.exists():
                backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(self.data_file, self.backup_dir / backup_name)
            
            self.data["metadata"]["last_modified"] = datetime.datetime.now().isoformat()
            self.data["metadata"]["total_potions"] = len(self.data["potions"])
            self.data["metadata"]["total_ingredients"] = len(self.data["ingredients"])
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder: {e}")


# ==================== POTION MANAGER ====================

class PotionManager:
    """Gestionnaire principal des potions"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.data = self.data_manager.data
    
    def get_bases(self) -> List[Base]:
        """Obtenir toutes les bases"""
        return [Base(**base_data) for base_data in self.data["bases"].values()]
    
    def get_ingredients(self, filter_type: str = None) -> List[Ingredient]:
        """Obtenir les ingrédients, optionnellement filtrés par type"""
        ingredients = []
        
        # Debug
        print(f"DEBUG get_ingredients: filter_type={filter_type}")
        print(f"DEBUG get_ingredients: nombre d'ingrédients dans data = {len(self.data['ingredients'])}")
        
        for ing_id, ing_data in self.data["ingredients"].items():
            try:
                # Vérifier que toutes les clés nécessaires sont présentes
                required_keys = ["id", "name", "effect", "type", "quality", "duration"]
                missing_keys = [key for key in required_keys if key not in ing_data]
                
                if missing_keys:
                    print(f"DEBUG: Ingrédient {ing_id} manque les clés: {missing_keys}")
                    continue
                
                if filter_type is None or ing_data["type"] == filter_type:
                    ingredient = Ingredient(**ing_data)
                    ingredients.append(ingredient)
                    
            except Exception as e:
                print(f"DEBUG: Erreur lors de la création de l'ingrédient {ing_id}: {e}")
                print(f"DEBUG: Données de l'ingrédient: {ing_data}")
                continue
        
        print(f"DEBUG get_ingredients: {len(ingredients)} ingrédients créés avec succès")
        return sorted(ingredients, key=lambda x: x.name)
    
    def get_potions(self) -> List[Potion]:
        """Obtenir toutes les potions"""
        return [Potion(**potion_data) for potion_data in self.data["potions"].values()]
    
    def create_potion(self, base_id: str, ingredient1_id: str, ingredient2_id: str) -> Optional[Potion]:
        """Créer une nouvelle potion"""
        # Vérifier les doublons
        test_key = f"{base_id}|{min(ingredient1_id, ingredient2_id)}|{max(ingredient1_id, ingredient2_id)}"
        for potion in self.get_potions():
            if potion.get_key() == test_key:
                return None  # Doublon détecté
        
        # Obtenir les données
        base = self.data["bases"][base_id]
        ing1 = self.data["ingredients"][ingredient1_id]
        ing2 = self.data["ingredients"][ingredient2_id]
        
        # Déterminer la catégorie
        qual1, qual2 = ing1["quality"], ing2["quality"]
        category = qual1 if qual1 == qual2 else random.choice([qual1, qual2])
        
        # Générer le nom
        effect1, effect2 = ing1["effect"], ing2["effect"]
        if base["potion_type"] == "Médicament":
            name = f"{base['potion_type']} : {category} de {effect1} et {effect2}"
        else:
            name = f"{base['potion_type']} {category} de {effect1} et {effect2}"
        
        # Créer la potion
        potion_id = f"potion_{len(self.data['potions']) + 1}"
        potion = Potion(
            id=potion_id,
            name=name,
            base=base_id,
            ingredient1=ingredient1_id,
            ingredient2=ingredient2_id,
            category=category,
            created_at=datetime.datetime.now().isoformat()
        )
        
        # Sauvegarder
        self.data["potions"][potion_id] = asdict(potion)
        self.data_manager.save_data()
        
        return potion
    
    def delete_potion(self, potion_id: str) -> bool:
        """Supprimer une potion"""
        if potion_id in self.data["potions"]:
            del self.data["potions"][potion_id]
            self.data_manager.save_data()
            return True
        return False
    
    def toggle_favorite(self, potion_id: str) -> bool:
        """Basculer le statut favori d'une potion"""
        if potion_id in self.data["potions"]:
            current = self.data["potions"][potion_id]["is_favorite"]
            self.data["potions"][potion_id]["is_favorite"] = not current
            self.data_manager.save_data()
            return not current
        return False
    
    def update_potion_notes(self, potion_id: str, notes: str):
        """Mettre à jour les notes d'une potion"""
        if potion_id in self.data["potions"]:
            self.data["potions"][potion_id]["notes"] = notes
            self.data_manager.save_data()
    
    def get_statistics(self) -> dict:
        """Obtenir les statistiques"""
        potions = self.get_potions()
        ingredients = self.get_ingredients()
        
        # Compteurs par catégorie
        categories = {}
        bases_used = {}
        ingredient_usage = {}
        
        for potion in potions:
            # Catégories
            categories[potion.category] = categories.get(potion.category, 0) + 1
            
            # Bases
            bases_used[potion.base] = bases_used.get(potion.base, 0) + 1
            
            # Ingrédients
            for ing_id in [potion.ingredient1, potion.ingredient2]:
                ingredient_usage[ing_id] = ingredient_usage.get(ing_id, 0) + 1
        
        return {
            "total_potions": len(potions),
            "total_ingredients": len(ingredients),
            "favorites": len([p for p in potions if p.is_favorite]),
            "categories": categories,
            "bases_used": bases_used,
            "ingredient_usage": ingredient_usage,
            "most_used_ingredient": max(ingredient_usage.items(), key=lambda x: x[1]) if ingredient_usage else None
        }

# ==================== INGREDIENT MANAGEMENT ====================

class IngredientEditorDialog:
    """Dialog pour créer/éditer un ingrédient avec types de potions autorisés"""
    
    def __init__(self, parent, potion_manager, ingredient=None):
        self.parent = parent
        self.potion_manager = potion_manager
        self.ingredient = ingredient
        self.result = None
        
        # Types de potions disponibles (extraits des bases)
        self.potion_types = []
        for base_data in potion_manager.data["bases"].values():
            if base_data["potion_type"] not in self.potion_types:
                self.potion_types.append(base_data["potion_type"])
        
        self.potion_type_vars = {}  # Dict pour stocker les variables des checkbox
        
        # Créer la fenêtre
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Éditer Ingrédient" if ingredient else "Nouvel Ingrédient")
        self.dialog.geometry("500x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self._create_widgets()
        self._populate_if_editing()
        
        # Focus sur le premier champ
        self.name_entry.focus_set()
    
    def _create_widgets(self):
        """Créer les widgets du formulaire"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title = "Modifier l'ingrédient" if self.ingredient else "Créer un nouvel ingrédient"
        ttk.Label(main_frame, text=title, font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Formulaire
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nom
        ttk.Label(form_frame, text="Nom de l'ingrédient *").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Effet
        ttk.Label(form_frame, text="Effet *").grid(row=1, column=0, sticky='w', pady=5)
        self.effect_var = tk.StringVar()
        self.effect_entry = ttk.Entry(form_frame, textvariable=self.effect_var, width=40)
        self.effect_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Type
        ttk.Label(form_frame, text="Type *").grid(row=2, column=0, sticky='w', pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, 
                                 values=["positif", "négatif"], state="readonly", width=37)
        type_combo.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Qualité
        ttk.Label(form_frame, text="Qualité *").grid(row=3, column=0, sticky='w', pady=5)
        self.quality_var = tk.StringVar()
        quality_combo = ttk.Combobox(form_frame, textvariable=self.quality_var,
                                    values=["Mineur", "Majeur", "Légendaire", "Mythique"], 
                                    state="readonly", width=37)
        quality_combo.grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Durée
        ttk.Label(form_frame, text="Durée *").grid(row=4, column=0, sticky='w', pady=5)
        self.duration_var = tk.StringVar()
        duration_combo = ttk.Combobox(form_frame, textvariable=self.duration_var,
                                     values=["Instantané", "1 minute", "10 minutes", "15 minutes", "1 heure", "24 heures", 
                                            "Un cycle", "Jusqu'à réveil", "Jusqu'à guérison",
                                            "Voir scénarisation"], width=37)
        duration_combo.grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Rareté
        ttk.Label(form_frame, text="Rareté").grid(row=5, column=0, sticky='w', pady=5)
        self.rarity_var = tk.StringVar(value="Commun")
        rarity_combo = ttk.Combobox(form_frame, textvariable=self.rarity_var,
                                   values=["Commun", "Rare", "Légendaire", "Mythique"], 
                                   state="readonly", width=37)
        rarity_combo.grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Description
        ttk.Label(form_frame, text="Description").grid(row=6, column=0, sticky='nw', pady=5)
        desc_frame = ttk.Frame(form_frame)
        desc_frame.grid(row=6, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        self.description_text = tk.Text(desc_frame, height=4, width=40, wrap=tk.WORD)
        desc_scrollbar = ttk.Scrollbar(desc_frame, command=self.description_text.yview)
        self.description_text.config(yscrollcommand=desc_scrollbar.set)
        
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Types de potions autorisés
        ttk.Label(form_frame, text="Utilisable dans *").grid(row=7, column=0, sticky='nw', pady=5)
        types_frame = ttk.LabelFrame(form_frame, text="Types de potions")
        types_frame.grid(row=7, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Créer les checkbox pour chaque type de potion
        for i, potion_type in enumerate(self.potion_types):
            var = tk.BooleanVar(value=True)  # Par défaut, tous cochés
            self.potion_type_vars[potion_type] = var
            
            check = ttk.Checkbutton(types_frame, text=potion_type, variable=var,
                                   command=self._validate_potion_types)
            check.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
        
        # Configuration de la grille
        form_frame.columnconfigure(1, weight=1)
        
        # Message d'aide
        help_frame = ttk.Frame(main_frame)
        help_frame.pack(fill=tk.X, pady=(20, 10))
        
        help_text = "* Champs obligatoires\nSélectionnez au moins un type de potion."
        ttk.Label(help_frame, text=help_text, font=('Arial', 8), foreground='gray').pack(anchor='w')
        
        # Status
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground='red')
        self.status_label.pack(pady=5)
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="Annuler", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        self.save_btn = ttk.Button(buttons_frame, text="Sauvegarder", command=self._save)
        self.save_btn.pack(side=tk.RIGHT)
        
        if self.ingredient:  # Mode édition
            ttk.Button(buttons_frame, text="Supprimer", command=self._delete).pack(side=tk.LEFT)
        
        # Validation en temps réel
        self.name_var.trace('w', self._validate)
        self.effect_var.trace('w', self._validate)
        self.type_var.trace('w', self._validate)
        self.quality_var.trace('w', self._validate)
        self.duration_var.trace('w', self._validate)
        
        # Bindings
        self.dialog.bind('<Return>', lambda e: self._save())
        self.dialog.bind('<Escape>', lambda e: self._cancel())
    
    def _populate_if_editing(self):
        """Remplir les champs si on édite un ingrédient existant"""
        if self.ingredient:
            self.name_var.set(self.ingredient.name)
            self.effect_var.set(self.ingredient.effect)
            self.type_var.set(self.ingredient.type)
            self.quality_var.set(self.ingredient.quality)
            self.duration_var.set(self.ingredient.duration)
            self.rarity_var.set(self.ingredient.rarity)
            
            self.description_text.insert(1.0, self.ingredient.description)
            
            # Configurer les checkbox selon les types autorisés
            for potion_type in self.potion_types:
                if hasattr(self.ingredient, 'allowed_potion_types'):
                    is_allowed = potion_type in self.ingredient.allowed_potion_types
                else:
                    is_allowed = True  # Par défaut, tous autorisés pour les anciens ingrédients
                self.potion_type_vars[potion_type].set(is_allowed)
    
    def _validate_potion_types(self):
        """Valider qu'au moins un type de potion est sélectionné"""
        selected_count = sum(1 for var in self.potion_type_vars.values() if var.get())
        if selected_count == 0:
            self.status_var.set("Sélectionnez au moins un type de potion")
            self.save_btn.config(state="disabled")
            return False
        return True
    
    def _validate(self, *args):
        """Valider le formulaire"""
        name = self.name_var.get().strip()
        effect = self.effect_var.get().strip()
        type_val = self.type_var.get()
        quality = self.quality_var.get()
        duration = self.duration_var.get()
        
        if not all([name, effect, type_val, quality, duration]):
            self.status_var.set("Veuillez remplir tous les champs obligatoires")
            self.save_btn.config(state="disabled")
            return
        
        # Vérifier qu'au moins un type de potion est sélectionné
        if not self._validate_potion_types():
            return
        
        # Vérifier les doublons (sauf si on édite le même ingrédient)
        ingredient_id = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        existing_ids = list(self.potion_manager.data["ingredients"].keys())
        
        if self.ingredient:
            # Mode édition : autoriser le même ID que l'ingrédient actuel
            if ingredient_id in existing_ids and ingredient_id != self.ingredient.id:
                self.status_var.set("Un ingrédient avec ce nom existe déjà")
                self.save_btn.config(state="disabled")
                return
        else:
            # Mode création : aucun doublon autorisé
            if ingredient_id in existing_ids:
                self.status_var.set("Un ingrédient avec ce nom existe déjà")
                self.save_btn.config(state="disabled")
                return
        
        # Valide
        self.status_var.set("")
        self.save_btn.config(state="normal")
    
    def _save(self):
        """Sauvegarder l'ingrédient"""
        try:
            # Récupérer les données
            name = self.name_var.get().strip()
            effect = self.effect_var.get().strip()
            type_val = self.type_var.get()
            quality = self.quality_var.get()
            duration = self.duration_var.get()
            rarity = self.rarity_var.get()
            description = self.description_text.get(1.0, tk.END).strip()
            
            # Récupérer les types de potions autorisés
            allowed_potion_types = [pt for pt, var in self.potion_type_vars.items() if var.get()]
            
            # Générer l'ID
            ingredient_id = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
            
            # Créer l'objet ingrédient
            ingredient_data = {
                "id": ingredient_id,
                "name": name,
                "effect": effect,
                "type": type_val,
                "quality": quality,
                "duration": duration,
                "rarity": rarity,
                "description": description,
                "allowed_potion_types": allowed_potion_types
            }
            
            if self.ingredient:
                # Mode édition : mettre à jour
                old_id = self.ingredient.id
                
                # Si l'ID a changé, il faut mettre à jour toutes les références
                if old_id != ingredient_id:
                    # Supprimer l'ancien
                    del self.potion_manager.data["ingredients"][old_id]
                    
                    # Mettre à jour les potions qui utilisent cet ingrédient
                    for potion_data in self.potion_manager.data["potions"].values():
                        if potion_data["ingredient1"] == old_id:
                            potion_data["ingredient1"] = ingredient_id
                        if potion_data["ingredient2"] == old_id:
                            potion_data["ingredient2"] = ingredient_id
                
                # Ajouter/mettre à jour le nouveau
                self.potion_manager.data["ingredients"][ingredient_id] = ingredient_data
                
            else:
                # Mode création : ajouter
                self.potion_manager.data["ingredients"][ingredient_id] = ingredient_data
            
            # Sauvegarder
            self.potion_manager.data_manager.save_data()
            
            # Résultat pour le parent
            self.result = Ingredient(**ingredient_data)
            
            # Fermer
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder l'ingrédient: {e}")
    
    def _delete(self):
        """Supprimer l'ingrédient"""
        # ... (code existant reste identique)
        pass
    
    def _cancel(self):
        """Annuler"""
        self.dialog.destroy()

class IngredientManagerDialog:
    """Dialog principal de gestion des ingrédients"""
    
    def __init__(self, parent, potion_manager):
        self.parent = parent
        self.potion_manager = potion_manager
        
        # Créer la fenêtre
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Gestionnaire d'Ingrédients")
        self.dialog.geometry("1100x600")
        self.dialog.transient(parent)
        
        # Variables
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Tous")
        self.sort_var = tk.StringVar(value="Nom")
        
        self._create_widgets()
        self._refresh_list()
        
        # Centrer
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 50))
    
    def _create_widgets(self):
        """Créer l'interface"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        ttk.Label(main_frame, text="Gestionnaire d'Ingrédients", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Contrôles
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Recherche
        ttk.Label(controls_frame, text="Recherche:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        
        # Filtre par type
        ttk.Label(controls_frame, text="Type:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var,
                                   values=["Tous", "positif", "négatif"], 
                                   state="readonly", width=15)
        filter_combo.grid(row=0, column=3, sticky='ew', padx=(0, 10))
        
        # Tri
        ttk.Label(controls_frame, text="Trier par:").grid(row=0, column=4, sticky='w', padx=(0, 5))
        sort_combo = ttk.Combobox(controls_frame, textvariable=self.sort_var,
                                 values=["Nom", "Type", "Qualité", "Rareté"], 
                                 state="readonly", width=15)
        sort_combo.grid(row=0, column=5, sticky='ew')
        
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(3, weight=1)
        controls_frame.columnconfigure(5, weight=1)
        
        # Liste des ingrédients
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview
        columns = ("name", "effect", "type", "quality", "rarity", "bases")
        self.ingredients_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # En-têtes
        self.ingredients_tree.heading("name", text="Nom")
        self.ingredients_tree.heading("effect", text="Effet")
        self.ingredients_tree.heading("type", text="Type")
        self.ingredients_tree.heading("quality", text="Qualité")
        self.ingredients_tree.heading("rarity", text="Rareté")
        self.ingredients_tree.heading("bases", text="Bases compatibles")
        
        # Largeurs
        self.ingredients_tree.column("name", width=150, minwidth=120)
        self.ingredients_tree.column("effect", width=200, minwidth=150)
        self.ingredients_tree.column("type", width=70, minwidth=50)
        self.ingredients_tree.column("quality", width=80, minwidth=60)
        self.ingredients_tree.column("rarity", width=80, minwidth=60)
        self.ingredients_tree.column("bases", width=200, minwidth=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ingredients_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.ingredients_tree.xview)
        self.ingredients_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        self.ingredients_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Boutons d'action
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Nouvel Ingrédient", command=self._new_ingredient).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Modifier", command=self._edit_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Actualiser", command=self._refresh_list).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Fermer", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Statistiques
        self.stats_var = tk.StringVar()
        ttk.Label(buttons_frame, textvariable=self.stats_var).pack(side=tk.RIGHT, padx=(0, 20))
        
        # Bindings
        self.search_var.trace('w', lambda *args: self._refresh_list())
        self.filter_var.trace('w', lambda *args: self._refresh_list())
        self.sort_var.trace('w', lambda *args: self._refresh_list())
        
        self.ingredients_tree.bind("<Double-1>", lambda e: self._edit_ingredient())
        self.ingredients_tree.bind("<Return>", lambda e: self._edit_ingredient())
    
    def _refresh_list(self):
        """Actualiser la liste des ingrédients"""
        # Debug: Vérifier les données
        print(f"DEBUG: Nombre total d'ingrédients dans les données: {len(self.potion_manager.data['ingredients'])}")
        
        # Vider la liste
        for item in self.ingredients_tree.get_children():
            self.ingredients_tree.delete(item)
        
        # Obtenir et filtrer les ingrédients
        ingredients = self.potion_manager.get_ingredients()
        print(f"DEBUG: Ingrédients récupérés par get_ingredients(): {len(ingredients)}")
        
        if ingredients:
            print(f"DEBUG: Premier ingrédient: {ingredients[0].name} - {ingredients[0].type}")
        
        filtered_ingredients = self._filter_ingredients(ingredients)
        sorted_ingredients = self._sort_ingredients(filtered_ingredients)
        
        print(f"DEBUG: Ingrédients après filtrage: {len(filtered_ingredients)}")
        print(f"DEBUG: Ingrédients après tri: {len(sorted_ingredients)}")
        
        # Remplir la liste
        for ingredient in sorted_ingredients:
            # Couleur selon le type
            tags = (ingredient.type,)
            
            # Formater les bases compatibles
            base_names = {
                "eau": "Potion",
                "huile": "Poison", 
                "pate": "Onguent",
                "vin": "Filtre",
                "cendre": "Substrat",
                "quartz": "Médicament"
            }
            
            compatible_bases = getattr(ingredient, 'compatible_bases', [])
            bases_display = ", ".join([base_names.get(base, base) for base in compatible_bases])
            if not bases_display:
                bases_display = "Aucune"
            
            self.ingredients_tree.insert("", tk.END,
                                       values=(ingredient.name, ingredient.effect, 
                                             ingredient.type, ingredient.quality, 
                                             ingredient.rarity, bases_display),
                                       tags=tags)
        
        # Configuration des couleurs
        self.ingredients_tree.tag_configure("positif", background="#e8f5e8")
        self.ingredients_tree.tag_configure("négatif", background="#fde8e8")
        
        # Statistiques
        total = len(ingredients)
        displayed = len(sorted_ingredients)
        positifs = len([i for i in sorted_ingredients if i.type == "positif"])
        negatifs = len([i for i in sorted_ingredients if i.type == "négatif"])
        
        stats_text = f"Total: {total} | Affichés: {displayed} | Positifs: {positifs} | Négatifs: {negatifs}"
        self.stats_var.set(stats_text)

    def _new_ingredient(self):
        """Créer un nouvel ingrédient via le dialog"""
        editor = IngredientEditorDialog(self.dialog, self.potion_manager)
        self.dialog.wait_window(editor.dialog)

        if editor.result:
            self._refresh_list()
            messagebox.showinfo("Succès", f"Ingrédient '{editor.result.name}' créé avec succès !")
            self.dialog.event_generate("<<IngredientsChanged>>", when="tail")

    def _edit_ingredient(self):
        """Modifier l'ingrédient sélectionné"""
        selection = self.ingredients_tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ingrédient à modifier.")
            return

        item = selection[0]
        name = self.ingredients_tree.item(item, "values")[0]

        # Trouver l'ingrédient par son nom
        for ing in self.potion_manager.get_ingredients():
            if ing.name == name:
                editor = IngredientEditorDialog(self.dialog, self.potion_manager, ingredient=ing)
                self.dialog.wait_window(editor.dialog)

                if editor.result:
                    self._refresh_list()
                    messagebox.showinfo("Succès", f"Ingrédient '{editor.result.name}' modifié avec succès !")
                    self.dialog.event_generate("<<IngredientsChanged>>", when="tail")
                break

    def _filter_ingredients(self, ingredients):
        """Appliquer les filtres de recherche et de type aux ingrédients"""
        search_text = self.search_var.get().lower()
        filter_type = self.filter_var.get()

        filtered = []
        for ing in ingredients:
            if search_text and search_text not in ing.name.lower():
                continue
            if filter_type != "Tous" and ing.type != filter_type:
                continue
            filtered.append(ing)

        return filtered

    def _sort_ingredients(self, ingredients):
        """Trier les ingrédients selon le critère sélectionné"""
        sort_key = self.sort_var.get()

        if sort_key == "Nom":
            return sorted(ingredients, key=lambda i: i.name.lower())
        elif sort_key == "Type":
            return sorted(ingredients, key=lambda i: i.type)
        elif sort_key == "Qualité":
            return sorted(ingredients, key=lambda i: i.quality)
        elif sort_key == "Rareté":
            return sorted(ingredients, key=lambda i: i.rarity)

        return ingredients

class SearchableCombobox(ttk.Frame):
    """Combobox avec recherche intégrée"""
    
    def __init__(self, parent, values=None, **kwargs):
        super().__init__(parent)
        self.values = values or []
        self.filtered_values = self.values.copy()
        
        # Variable pour la sélection
        self.var = tk.StringVar()
        
        # Entry pour la recherche
        self.entry = ttk.Entry(self, textvariable=self.var)
        self.entry.pack(fill=tk.X)
        
        # Listbox pour les résultats
        self.listbox = tk.Listbox(self, height=6)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        # Bindings
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.listbox.bind('<Double-Button-1>', self._on_select)
        self.listbox.bind('<Return>', self._on_select)
        
        self._update_listbox()
    
    def _on_key_release(self, event):
        """Filtrer les résultats lors de la saisie"""
        search_term = self.var.get().lower()
        self.filtered_values = [v for v in self.values if search_term in v.lower()]
        self._update_listbox()
        
        # Auto-sélection si un seul résultat
        if len(self.filtered_values) == 1:
            self.listbox.selection_set(0)
    
    def _on_select(self, event):
        """Sélectionner un élément"""
        selection = self.listbox.curselection()
        if selection:
            value = self.filtered_values[selection[0]]
            self.var.set(value)
    
    def _update_listbox(self):
        """Mettre à jour la listbox"""
        self.listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self.listbox.insert(tk.END, value)
    
    def set_values(self, values):
        """Définir les valeurs disponibles"""
        self.values = values
        self.filtered_values = values.copy()
        self._update_listbox()
    
    def get(self):
        """Obtenir la valeur sélectionnée"""
        return self.var.get()
    
    def set(self, value):
        """Définir la valeur"""
        self.var.set(value)

class PotionDetailsPanel(ttk.Frame):
    """Panel d'affichage des détails d'une potion"""
    
    def __init__(self, parent, potion_manager):
        super().__init__(parent)
        self.potion_manager = potion_manager
        self.current_potion = None
        
        # Titre
        self.title_var = tk.StringVar()
        title_label = ttk.Label(self, textvariable=self.title_var, font=('Arial', 14, 'bold'))
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Informations principales
        self.info_frame = ttk.LabelFrame(self, text="Informations")
        self.info_frame.pack(fill=tk.X, pady=5)
        
        self.category_var = tk.StringVar()
        self.base_var = tk.StringVar()
        self.created_var = tk.StringVar()
        
        ttk.Label(self.info_frame, textvariable=self.category_var).pack(anchor='w', padx=5, pady=2)
        ttk.Label(self.info_frame, textvariable=self.base_var).pack(anchor='w', padx=5, pady=2)
        ttk.Label(self.info_frame, textvariable=self.created_var).pack(anchor='w', padx=5, pady=2)
        
        # Ingrédients
        self.ingredients_frame = ttk.LabelFrame(self, text="Ingrédients")
        self.ingredients_frame.pack(fill=tk.X, pady=5)
        
        self.ingredient1_var = tk.StringVar()
        self.ingredient2_var = tk.StringVar()
        
        ttk.Label(self.ingredients_frame, textvariable=self.ingredient1_var, foreground='green').pack(anchor='w', padx=5, pady=2)
        ttk.Label(self.ingredients_frame, textvariable=self.ingredient2_var, foreground='red').pack(anchor='w', padx=5, pady=2)
        
        # Notes
        notes_frame = ttk.LabelFrame(self, text="Notes")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.notes_text = tk.Text(notes_frame, height=4, wrap=tk.WORD)
        notes_scrollbar = ttk.Scrollbar(notes_frame, command=self.notes_text.yview)
        self.notes_text.config(yscrollcommand=notes_scrollbar.set)
        
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Boutons d'action
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, pady=5)
        
        self.favorite_btn = ttk.Button(actions_frame, text="★ Favori", command=self._toggle_favorite)
        self.favorite_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(actions_frame, text="Sauver Notes", command=self._save_notes).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Supprimer", command=self._delete_potion).pack(side=tk.RIGHT)
        
        # Binding pour les notes
        self.notes_text.bind('<KeyRelease>', self._on_notes_change)
    
    def display_potion(self, potion: Potion):
        """Afficher les détails d'une potion"""
        self.current_potion = potion
        
        # Titre
        self.title_var.set(potion.name)
        
        # Informations
        self.category_var.set(f"Catégorie : {potion.category}")
        base_name = self.potion_manager.data["bases"][potion.base]["name"]
        self.base_var.set(f"Base : {base_name}")
        
        created_date = datetime.datetime.fromisoformat(potion.created_at).strftime("%d/%m/%Y %H:%M")
        self.created_var.set(f"Créée le : {created_date}")
        
        # Ingrédients
        ing1 = self.potion_manager.data["ingredients"][potion.ingredient1]
        ing2 = self.potion_manager.data["ingredients"][potion.ingredient2]
        
        self.ingredient1_var.set(f"✓ {ing1['name']} ({ing1['effect']}, {ing1['quality']}, {ing1['duration']})")
        self.ingredient2_var.set(f"✗ {ing2['name']} ({ing2['effect']}, {ing2['quality']}, {ing2['duration']})")
        
        # Notes
        self.notes_text.delete(1.0, tk.END)
        self.notes_text.insert(1.0, potion.notes)
        
        # Bouton favori
        self.favorite_btn.config(text="★ Favori" if potion.is_favorite else "☆ Favori")
    
    def clear(self):
        """Effacer l'affichage"""
        self.current_potion = None
        for var in [self.title_var, self.category_var, self.base_var, self.created_var, 
                   self.ingredient1_var, self.ingredient2_var]:
            var.set("")
        self.notes_text.delete(1.0, tk.END)
    
    def _toggle_favorite(self):
        """Basculer le statut favori"""
        if self.current_potion:
            new_status = self.potion_manager.toggle_favorite(self.current_potion.id)
            self.favorite_btn.config(text="★ Favori" if new_status else "☆ Favori")
            self.current_potion.is_favorite = new_status
    
    def _save_notes(self):
        """Sauvegarder les notes"""
        if self.current_potion:
            notes = self.notes_text.get(1.0, tk.END).strip()
            self.potion_manager.update_potion_notes(self.current_potion.id, notes)
            messagebox.showinfo("Succès", "Notes sauvegardées !")
    
    def _delete_potion(self):
        """Supprimer la potion"""
        if self.current_potion:
            result = messagebox.askyesno("Confirmation", 
                                       f"Êtes-vous sûr de vouloir supprimer '{self.current_potion.name}' ?")
            if result:
                self.potion_manager.delete_potion(self.current_potion.id)
                self.clear()
                messagebox.showinfo("Succès", "Potion supprimée !")
                # Notifier le parent pour rafraîchir la liste
                self.event_generate("<<PotionDeleted>>")
    
    def _on_notes_change(self, event):
        """Indiquer que les notes ont changé"""
        pass  # Ici on pourrait ajouter un indicateur de modification

# ==================== MAIN APPLICATION ====================

class PotionGeneratorApp:
    """Application principale du générateur de potions"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Générateur de Potions Avancé - v2.0")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        
        # Gestionnaire principal
        self.potion_manager = PotionManager()
        
        # Variables d'interface
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Nom")
        self.filter_var = tk.StringVar(value="Toutes")
        
        # Créer l'interface
        self._create_menu()
        self._create_ui()
        self._bind_events()
        
        # Initialiser l'affichage
        self._refresh_all()
    
    def _create_menu(self):
        """Créer la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Exporter CSV", command=self._export_csv)
        file_menu.add_command(label="Exporter JSON", command=self._export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Importer", command=self._import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Ingrédients
        ingredients_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ingrédients", menu=ingredients_menu)
        ingredients_menu.add_command(label="Gestionnaire d'Ingrédients", command=self._open_ingredient_manager)
        ingredients_menu.add_command(label="Nouvel Ingrédient", command=self._new_ingredient_quick)
        ingredients_menu.add_separator()
        ingredients_menu.add_command(label="Importer Ingrédients", command=self._import_ingredients)
        ingredients_menu.add_command(label="Exporter Ingrédients", command=self._export_ingredients)
        
        # Menu Outils  
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Statistiques", command=self._show_statistics)
        tools_menu.add_command(label="Nettoyage", command=self._cleanup_data)
        tools_menu.add_command(label="Vérifier Cohérence", command=self._check_data_integrity)
        tools_menu.add_separator()
        tools_menu.add_command(label="Debug Info", command=self._show_debug_info)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Guide", command=self._show_help)
        help_menu.add_command(label="À propos", command=self._show_about)
    
    def _create_ui(self):
        """Créer l'interface utilisateur"""
        # Conteneur principal avec panneaux redimensionnables
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel gauche - Création
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Panel droit avec sous-panneaux
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        main_paned.add(right_paned, weight=2)
        
        # Panel liste des potions
        list_frame = ttk.Frame(right_paned)
        right_paned.add(list_frame, weight=1)
        
        # Panel détails
        details_frame = ttk.Frame(right_paned)
        right_paned.add(details_frame, weight=1)
        
        # Créer les sections 
        self._create_creation_panel(left_frame)
        self._create_list_panel(list_frame)
        self._create_details_panel(details_frame)
    
    def _create_creation_panel(self, parent):
        """Créer le panel de création de potions"""
        # Titre
        title_label = ttk.Label(parent, text="Création de Potion", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Base
        base_frame = ttk.LabelFrame(parent, text="Base de la potion")
        base_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.base_var = tk.StringVar()
        bases = self.potion_manager.get_bases()
        base_values = [f"{base.name} ({base.potion_type})" for base in bases]
        
        self.base_combo = ttk.Combobox(base_frame, textvariable=self.base_var, 
                                      values=base_values, state="readonly")
        self.base_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Ingrédient positif
        pos_frame = ttk.LabelFrame(parent, text="Ingrédient (Effet positif)")
        pos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.pos_search = SearchableCombobox(pos_frame)
        self.pos_search.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ingrédient négatif
        neg_frame = ttk.LabelFrame(parent, text="Ingrédient (Effet négatif)")
        neg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.neg_search = SearchableCombobox(neg_frame)
        self.neg_search.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status et boutons
        self.status_var = tk.StringVar()
        status_label = ttk.Label(parent, textvariable=self.status_var, foreground='red')
        status_label.pack(pady=5)
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.create_btn = ttk.Button(buttons_frame, text="Créer Potion", 
                                    command=self._create_potion, state="disabled")
        self.create_btn.pack(fill=tk.X, pady=2)
        
        ttk.Button(buttons_frame, text="Réinitialiser", 
                  command=self._reset_form).pack(fill=tk.X, pady=2)
        
        ttk.Button(buttons_frame, text="Suggestion Aléatoire", 
                  command=self._random_suggestion).pack(fill=tk.X, pady=2)
    
    def _create_list_panel(self, parent):
        """Créer le panel de liste des potions"""
        # Titre et contrôles
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Liste des Potions", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Contrôles de recherche et tri
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Recherche
        ttk.Label(controls_frame, text="Recherche:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        
        # Tri
        ttk.Label(controls_frame, text="Trier par:").grid(row=0, column=2, sticky='w', padx=(0, 5))
        sort_combo = ttk.Combobox(controls_frame, textvariable=self.sort_var, 
                                 values=["Nom", "Catégorie", "Date", "Base"], 
                                 state="readonly", width=15)
        sort_combo.grid(row=0, column=3, sticky='ew', padx=(0, 10))
        
        # Filtre
        ttk.Label(controls_frame, text="Filtre:").grid(row=0, column=4, sticky='w', padx=(0, 5))
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var,
                                   values=["Toutes", "Favorites", "Mineur", "Majeur", "Légendaire", "Mythique"],
                                   state="readonly", width=15)
        filter_combo.grid(row=0, column=5, sticky='ew')
        
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(3, weight=1)
        controls_frame.columnconfigure(5, weight=1)
        
        # Liste des potions avec scrollbars
        list_container = ttk.Frame(parent)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview pour affichage tabulaire
        columns = ("name", "category", "base", "created")
        self.potions_tree = ttk.Treeview(list_container, columns=columns, show="tree headings", height=15)
        
        # Configuration des colonnes
        self.potions_tree.heading("#0", text="★")
        self.potions_tree.heading("name", text="Nom")
        self.potions_tree.heading("category", text="Catégorie") 
        self.potions_tree.heading("base", text="Base")
        self.potions_tree.heading("created", text="Créée le")
        
        self.potions_tree.column("#0", width=30, minwidth=30)
        self.potions_tree.column("name", width=300, minwidth=200)
        self.potions_tree.column("category", width=100, minwidth=80)
        self.potions_tree.column("base", width=100, minwidth=80)
        self.potions_tree.column("created", width=120, minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.potions_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_container, orient=tk.HORIZONTAL, command=self.potions_tree.xview)
        self.potions_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        self.potions_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # Statistiques en bas
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_var = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(side=tk.LEFT)
        
        ttk.Button(stats_frame, text="Actualiser", command=self._refresh_potions_list).pack(side=tk.RIGHT)
    
    def _create_details_panel(self, parent):
        """Créer le panel de détails"""
        self.details_panel = PotionDetailsPanel(parent, self.potion_manager)
        self.details_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _bind_events(self):
        """Lier les événements"""
        # Validation en temps réel pour la création
        self.base_combo.bind("<<ComboboxSelected>>", self._validate_creation)
        self.pos_search.var.trace('w', self._validate_creation)
        self.neg_search.var.trace('w', self._validate_creation)

        # Rafraîchir les ingrédients quand la base change
        self.base_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_ingredients())
        
        # Recherche et filtres
        self.search_var.trace('w', lambda *args: self._refresh_potions_list())
        self.sort_var.trace('w', lambda *args: self._refresh_potions_list())
        self.filter_var.trace('w', lambda *args: self._refresh_potions_list())
        
        # Sélection dans la liste
        self.potions_tree.bind("<<TreeviewSelect>>", self._on_potion_select)
        self.potions_tree.bind("<Double-1>", self._on_potion_double_click)
        
        # Suppression de potion et changements d'ingrédients
        self.details_panel.bind("<<PotionDeleted>>", lambda e: self._refresh_potions_list())
        self.root.bind("<<IngredientsChanged>>", lambda e: self._on_ingredients_changed())
        
        # Raccourcis clavier
        self.root.bind("<Control-n>", lambda e: self._create_potion())
        self.root.bind("<Control-r>", lambda e: self._reset_form())
        self.root.bind("<Control-s>", lambda e: self._export_csv())
        self.root.bind("<Control-i>", lambda e: self._open_ingredient_manager())
        self.root.bind("<F5>", lambda e: self._refresh_all())
        
        # Fermeture de l'application
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_ingredients_changed(self):
        """Réagir aux changements d'ingrédients"""
        self._refresh_ingredients()
        self._refresh_potions_list()
        self._validate_creation()
    
    def _open_ingredient_manager(self):
        """Ouvrir le gestionnaire d'ingrédients"""
        IngredientManagerDialog(self.root, self.potion_manager)
    
    def _new_ingredient_quick(self):
        """Créer rapidement un nouvel ingrédient"""
        editor = IngredientEditorDialog(self.root, self.potion_manager)
        self.root.wait_window(editor.dialog)
        
        if editor.result:
            self._on_ingredients_changed()
            messagebox.showinfo("Succès", f"Ingrédient '{editor.result.name}' créé avec succès !")
    
    def _import_ingredients(self):
        """Importer des ingrédients depuis un fichier JSON"""
        filepath = filedialog.askopenfilename(
            title="Importer des ingrédients",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    imported_data = json.load(f)
                
                imported_count = 0
                
                # Différents formats possibles
                if "ingredients" in imported_data:
                    # Format complet avec section ingredients
                    ingredients_data = imported_data["ingredients"]
                elif isinstance(imported_data, dict) and all(isinstance(v, dict) for v in imported_data.values()):
                    # Format direct dictionnaire d'ingrédients
                    ingredients_data = imported_data
                else:
                    messagebox.showerror("Format invalide", "Le fichier ne contient pas d'ingrédients au format attendu.")
                    return
                
                # Importer chaque ingrédient
                for ing_id, ing_data in ingredients_data.items():
                    try:
                        # Valider les champs obligatoires
                        required_fields = ["name", "effect", "type", "quality", "duration"]
                        if not all(field in ing_data for field in required_fields):
                            print(f"Ingrédient {ing_id} ignoré: champs manquants")
                            continue
                        
                        # Compléter les champs optionnels
                        ing_data.setdefault("id", ing_id)
                        ing_data.setdefault("rarity", "Commun")
                        ing_data.setdefault("description", "")
                        ing_data.setdefault("contraindications", [])
                        ing_data.setdefault("synergies", [])
                        
                        # Vérifier si l'ingrédient existe déjà
                        if ing_id in self.potion_manager.data["ingredients"]:
                            result = messagebox.askyesnocancel(
                                "Doublon détecté",
                                f"L'ingrédient '{ing_data['name']}' existe déjà. Remplacer ?",
                            )
                            if result is None:  # Cancel
                                break
                            elif not result:  # No
                                continue
                        
                        # Ajouter l'ingrédient
                        self.potion_manager.data["ingredients"][ing_id] = ing_data
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"Erreur lors de l'import de {ing_id}: {e}")
                        continue
                
                # Sauvegarder
                if imported_count > 0:
                    self.potion_manager.data_manager.save_data()
                    self._on_ingredients_changed()
                    messagebox.showinfo("Import terminé", f"{imported_count} ingrédient(s) importé(s) avec succès !")
                else:
                    messagebox.showwarning("Aucun import", "Aucun ingrédient n'a pu être importé.")
                
            except Exception as e:
                messagebox.showerror("Erreur d'import", f"Impossible d'importer les ingrédients: {e}")
    
    def _export_ingredients(self):
        """Exporter tous les ingrédients"""
        ingredients = self.potion_manager.get_ingredients()
        if not ingredients:
            messagebox.showinfo("Aucun ingrédient", "Aucun ingrédient à exporter.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")],
            initialname="ingredients_export.json"
        )
        
        if filepath:
            try:
                if filepath.endswith('.csv'):
                    # Export CSV
                    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Nom", "Effet", "Type", "Qualité", "Durée", "Rareté", "Description"])
                        
                        for ingredient in ingredients:
                            writer.writerow([
                                ingredient.name, ingredient.effect, ingredient.type,
                                ingredient.quality, ingredient.duration, ingredient.rarity,
                                ingredient.description
                            ])
                else:
                    # Export JSON
                    export_data = {
                        "version": "2.0",
                        "export_date": datetime.datetime.now().isoformat(),
                        "total_ingredients": len(ingredients),
                        "ingredients": self.potion_manager.data["ingredients"]
                    }
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export terminé", f"Ingrédients exportés dans {filepath}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Impossible d'exporter: {e}")
    
    def _show_debug_info(self):
        """Afficher les informations de débogage"""
        debug_info = []
        
        # Informations générales
        debug_info.append("=== INFORMATIONS DE DÉBOGAGE ===\n")
        debug_info.append(f"Version des données: {self.potion_manager.data.get('version', 'Non définie')}")
        debug_info.append(f"Fichier de données: {self.potion_manager.data_manager.data_file}")
        
        # Ingrédients
        debug_info.append(f"\n=== INGRÉDIENTS ===")
        debug_info.append(f"Nombre total dans le JSON: {len(self.potion_manager.data['ingredients'])}")
        
        ingredients = self.potion_manager.get_ingredients()
        debug_info.append(f"Nombre récupéré par get_ingredients(): {len(ingredients)}")
        
        if ingredients:
            debug_info.append(f"\nPremiers ingrédients:")
            for i, ing in enumerate(ingredients[:5]):
                debug_info.append(f"  {i+1}. {ing.name} ({ing.type}) - ID: {ing.id}")
        
        # Types d'ingrédients
        positifs = self.potion_manager.get_ingredients("positif")
        negatifs = self.potion_manager.get_ingredients("négatif")
        debug_info.append(f"\nIngrédients positifs: {len(positifs)}")
        debug_info.append(f"Ingrédients négatifs: {len(negatifs)}")
        
        # Potions
        potions = self.potion_manager.get_potions()
        debug_info.append(f"\n=== POTIONS ===")
        debug_info.append(f"Nombre total: {len(potions)}")
        
        # Bases
        bases = self.potion_manager.get_bases()
        debug_info.append(f"\n=== BASES ===")
        debug_info.append(f"Nombre total: {len(bases)}")
        for base in bases:
            debug_info.append(f"  - {base.name} ({base.id})")
        
        # Structure des données
        debug_info.append(f"\n=== STRUCTURE JSON ===")
        debug_info.append(f"Clés principales: {list(self.potion_manager.data.keys())}")
        
        if 'ingredients' in self.potion_manager.data:
            ingredient_ids = list(self.potion_manager.data['ingredients'].keys())
            debug_info.append(f"IDs des ingrédients (5 premiers): {ingredient_ids[:5]}")
        
        # Afficher dans une fenêtre
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Informations de Débogage")
        debug_window.geometry("800x600")
        debug_window.transient(self.root)
        
        text_widget = tk.Text(debug_window, wrap=tk.WORD, padx=10, pady=10, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(debug_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, '\n'.join(debug_info))
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _check_data_integrity(self):
        """Vérifier la cohérence des données"""
        issues = []
        
        # Vérifier les ingrédients
        for ing_id, ing_data in self.potion_manager.data["ingredients"].items():
            if ing_id != ing_data.get("id"):
                issues.append(f"Ingrédient {ing_id}: ID incohérent")
            
            required_fields = ["name", "effect", "type", "quality", "duration"]
            for field in required_fields:
                if not ing_data.get(field):
                    issues.append(f"Ingrédient {ing_id}: champ '{field}' manquant")
        
        # Vérifier les potions
        valid_ingredient_ids = set(self.potion_manager.data["ingredients"].keys())
        valid_base_ids = set(self.potion_manager.data["bases"].keys())
        
        for potion_id, potion_data in self.potion_manager.data["potions"].items():
            if potion_data.get("base") not in valid_base_ids:
                issues.append(f"Potion {potion_id}: base '{potion_data.get('base')}' invalide")
            
            for i, field in enumerate(["ingredient1", "ingredient2"], 1):
                ing_id = potion_data.get(field)
                if ing_id not in valid_ingredient_ids:
                    issues.append(f"Potion {potion_id}: ingrédient{i} '{ing_id}' invalide")
        
        # Afficher les résultats
        if issues:
            issues_text = "\n".join(issues[:20])  # Limiter l'affichage
            if len(issues) > 20:
                issues_text += f"\n... et {len(issues) - 20} autres problèmes"
            
            messagebox.showwarning("Problèmes détectés", 
                                 f"{len(issues)} problème(s) détecté(s):\n\n{issues_text}")
        else:
            messagebox.showinfo("Vérification terminée", "Aucun problème détecté. Les données sont cohérentes !")
    
    def _refresh_all(self):
        """Actualiser tous les éléments de l'interface"""
        self._refresh_ingredients()
        self._refresh_potions_list()
        self._validate_creation()
    
    def _refresh_ingredients(self):
        """Actualiser les listes d'ingrédients selon la base sélectionnée"""
        # Obtenir le type de potion sélectionné
        potion_type = None
        if self.base_var.get():
            base_id = self._extract_base_id(self.base_var.get())
            if base_id and base_id in self.potion_manager.data["bases"]:
                potion_type = self.potion_manager.data["bases"][base_id]["potion_type"]
        
        # Obtenir tous les ingrédients
        pos_ingredients = self.potion_manager.get_ingredients("positif")
        neg_ingredients = self.potion_manager.get_ingredients("négatif")
        
        # Filtrer selon le type de potion si une base est sélectionnée
        if potion_type:
            pos_ingredients = [ing for ing in pos_ingredients 
                             if potion_type in ing.allowed_potion_types]
            neg_ingredients = [ing for ing in neg_ingredients 
                             if potion_type in ing.allowed_potion_types]
        
        pos_names = [f"{ing.name} ({ing.effect})" for ing in pos_ingredients]
        neg_names = [f"{ing.name} ({ing.effect})" for ing in neg_ingredients]
        
        self.pos_search.set_values(pos_names)
        self.neg_search.set_values(neg_names)
    
    
    def _refresh_potions_list(self):
        """Actualiser la liste des potions"""
        # Vider la liste
        for item in self.potions_tree.get_children():
            self.potions_tree.delete(item)
        
        # Obtenir et filtrer les potions
        potions = self.potion_manager.get_potions()
        filtered_potions = self._filter_potions(potions)
        sorted_potions = self._sort_potions(filtered_potions)
        
        # Remplir la liste
        for potion in sorted_potions:
            # Formater la date
            created_date = datetime.datetime.fromisoformat(potion.created_at).strftime("%d/%m/%Y")
            
            # Obtenir le nom de la base
            base_name = self.potion_manager.data["bases"][potion.base]["name"]
            
            # Icône favorite
            favorite_icon = "★" if potion.is_favorite else ""
            
            # Insérer dans le treeview
            item_id = self.potions_tree.insert("", tk.END, 
                                              text=favorite_icon,
                                              values=(potion.name, potion.category, base_name, created_date),
                                              tags=(potion.id,))
        
        # Mettre à jour les statistiques
        self._update_statistics()
    
    def _filter_potions(self, potions: List[Potion]) -> List[Potion]:
        """Filtrer les potions selon les critères"""
        filtered = potions
        
        # Filtre par texte de recherche
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [p for p in filtered if search_text in p.name.lower()]
        
        # Filtre par catégorie/type
        filter_value = self.filter_var.get()
        if filter_value == "Favorites":
            filtered = [p for p in filtered if p.is_favorite]
        elif filter_value in ["Mineur", "Majeur", "Légendaire", "Mythique"]:
            filtered = [p for p in filtered if p.category == filter_value]
        
        return filtered
    
    def _sort_potions(self, potions: List[Potion]) -> List[Potion]:
        """Trier les potions"""
        sort_by = self.sort_var.get()
        
        if sort_by == "Nom":
            return sorted(potions, key=lambda p: p.name.lower())
        elif sort_by == "Catégorie":
            return sorted(potions, key=lambda p: p.category)
        elif sort_by == "Date":
            return sorted(potions, key=lambda p: p.created_at, reverse=True)
        elif sort_by == "Base":
            return sorted(potions, key=lambda p: p.base)
        
        return potions
    
    def _update_statistics(self):
        """Mettre à jour l'affichage des statistiques"""
        stats = self.potion_manager.get_statistics()
        total = stats["total_potions"]
        favorites = stats["favorites"]
        
        # Compter les potions affichées
        displayed = len(self.potions_tree.get_children())
        
        stats_text = f"Total: {total} potions | Affichées: {displayed} | Favorites: {favorites}"
        self.stats_var.set(stats_text)
    
    def _validate_creation(self, *args):
        """Valider la possibilité de créer une potion"""
        base = self.base_var.get()
        pos_ing = self.pos_search.get()
        neg_ing = self.neg_search.get()
        
        if not all([base, pos_ing, neg_ing]):
            self.status_var.set("Veuillez sélectionner tous les champs")
            self.create_btn.config(state="disabled")
            return
        
        # Extraire les IDs
        try:
            base_id = self._extract_base_id(base)
            pos_id = self._extract_ingredient_id(pos_ing, "positif")
            neg_id = self._extract_ingredient_id(neg_ing, "négatif")
            
            if not all([base_id, pos_id, neg_id]):
                raise ValueError("IDs non trouvés")
            
            # Vérifier que les ingrédients sont autorisés pour ce type de potion
            base_data = self.potion_manager.data["bases"][base_id]
            potion_type = base_data["potion_type"]
            
            pos_ingredient = self.potion_manager.data["ingredients"][pos_id]
            neg_ingredient = self.potion_manager.data["ingredients"][neg_id]
            
            # Vérifier les types autorisés
            pos_allowed = pos_ingredient.get("allowed_potion_types", [])
            neg_allowed = neg_ingredient.get("allowed_potion_types", [])
            
            if potion_type not in pos_allowed:
                self.status_var.set(f"{pos_ingredient['name']} n'est pas utilisable dans les {potion_type}s")
                self.create_btn.config(state="disabled")
                return
            
            if potion_type not in neg_allowed:
                self.status_var.set(f"{neg_ingredient['name']} n'est pas utilisable dans les {potion_type}s")
                self.create_btn.config(state="disabled")
                return
            
        except:
            self.status_var.set("Sélections invalides")
            self.create_btn.config(state="disabled")
            return
        
        # Vérifier les doublons
        test_key = f"{base_id}|{min(pos_id, neg_id)}|{max(pos_id, neg_id)}"
        for potion in self.potion_manager.get_potions():
            if potion.get_key() == test_key:
                self.status_var.set("Cette combinaison existe déjà")
                self.create_btn.config(state="disabled")
                return
        
        # Tout est valide
        self.status_var.set("Prêt à créer")
        self.create_btn.config(state="normal")
    
    def _extract_base_id(self, base_display: str) -> str:
        """Extraire l'ID de base depuis l'affichage"""
        base_name = base_display.split(" (")[0]
        for base_id, base_data in self.potion_manager.data["bases"].items():
            if base_data["name"] == base_name:
                return base_id
        return ""
    
    def _extract_ingredient_id(self, ingredient_display: str, expected_type: str) -> str:
        """Extraire l'ID d'ingrédient depuis l'affichage"""
        ingredient_name = ingredient_display.split(" (")[0]
        for ing_id, ing_data in self.potion_manager.data["ingredients"].items():
            if ing_data["name"] == ingredient_name and ing_data["type"] == expected_type:
                return ing_id
        return ""
    
    def _create_potion(self):
        """Créer une nouvelle potion"""
        try:
            base_id = self._extract_base_id(self.base_var.get())
            pos_id = self._extract_ingredient_id(self.pos_search.get(), "positif")
            neg_id = self._extract_ingredient_id(self.neg_search.get(), "négatif")
            
            potion = self.potion_manager.create_potion(base_id, pos_id, neg_id)
            
            if potion:
                messagebox.showinfo("Succès", f"Potion créée: {potion.name}")
                self._refresh_potions_list()
                self._reset_form()
            else:
                messagebox.showerror("Erreur", "Impossible de créer la potion (doublon?)")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création: {e}")
    
    def _reset_form(self):
        """Réinitialiser le formulaire de création"""
        self.base_var.set("")
        self.pos_search.set("")
        self.neg_search.set("")
        self.status_var.set("")
        self.create_btn.config(state="disabled")
    
    def _random_suggestion(self):
        """Suggérer une combinaison aléatoire"""
        bases = self.potion_manager.get_bases()
        pos_ingredients = self.potion_manager.get_ingredients("positif")
        neg_ingredients = self.potion_manager.get_ingredients("négatif")
        
        if bases and pos_ingredients and neg_ingredients:
            base = random.choice(bases)
            pos_ing = random.choice(pos_ingredients)
            neg_ing = random.choice(neg_ingredients)
            
            self.base_var.set(f"{base.name} ({base.potion_type})")
            self.pos_search.set(f"{pos_ing.name} ({pos_ing.effect})")
            self.neg_search.set(f"{neg_ing.name} ({neg_ing.effect})")
    
    def _on_potion_select(self, event):
        """Gestion de la sélection d'une potion"""
        selection = self.potions_tree.selection()
        if selection:
            item = selection[0]
            # L'ID de la potion est dans les tags
            potion_id = self.potions_tree.item(item, "tags")[0]
            
            # Trouver la potion
            for potion in self.potion_manager.get_potions():
                if potion.id == potion_id:
                    self.details_panel.display_potion(potion)
                    break
    
    def _on_potion_double_click(self, event):
        """Gestion du double-clic sur une potion"""
        # Ici on pourrait ouvrir une fenêtre d'édition détaillée
        pass
    
    def _export_csv(self):
        """Exporter les potions en CSV"""
        potions = self.potion_manager.get_potions()
        if not potions:
            messagebox.showinfo("Aucune potion", "Aucune potion à exporter.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname="potions_export.csv"
        )
        
        if filepath:
            try:
                with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Nom", "Base", "Catégorie", "Ingrédient1", "Ingrédient2", 
                                   "Créée le", "Favorite", "Notes"])
                    
                    for potion in potions:
                        base_name = self.potion_manager.data["bases"][potion.base]["name"]
                        ing1_name = self.potion_manager.data["ingredients"][potion.ingredient1]["name"]
                        ing2_name = self.potion_manager.data["ingredients"][potion.ingredient2]["name"]
                        created_date = datetime.datetime.fromisoformat(potion.created_at).strftime("%d/%m/%Y %H:%M")
                        
                        writer.writerow([
                            potion.name, base_name, potion.category, 
                            ing1_name, ing2_name, created_date,
                            "Oui" if potion.is_favorite else "Non",
                            potion.notes
                        ])
                
                messagebox.showinfo("Export terminé", f"Potions exportées dans {filepath}")
                
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Impossible d'exporter: {e}")
    
    def _export_json(self):
        """Exporter toutes les données en JSON"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialname="potions_backup.json"
        )
        
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.potion_manager.data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export terminé", f"Données exportées dans {filepath}")
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Impossible d'exporter: {e}")
    
    def _import_data(self):
        """Importer des données"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            result = messagebox.askyesno("Confirmation", 
                                       "L'import va remplacer toutes les données actuelles. Continuer ?")
            if result:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        imported_data = json.load(f)
                    
                    # Valider et migrer si nécessaire
                    self.potion_manager.data = self.potion_manager.data_manager._migrate_data(imported_data)
                    self.potion_manager.data_manager.save_data()
                    
                    messagebox.showinfo("Import terminé", "Données importées avec succès !")
                    self._refresh_all()
                    
                except Exception as e:
                    messagebox.showerror("Erreur d'import", f"Impossible d'importer: {e}")
    
    def _show_statistics(self):
        """Afficher les statistiques détaillées"""
        stats = self.potion_manager.get_statistics()
        
        # Créer une fenêtre de statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistiques")
        stats_window.geometry("600x400")
        stats_window.transient(self.root)
        
        # Notebook pour organiser les statistiques
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet général
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Général")
        
        ttk.Label(general_frame, text="Statistiques Générales", font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(general_frame, text=f"Total des potions: {stats['total_potions']}").pack(anchor='w', padx=20)
        ttk.Label(general_frame, text=f"Total des ingrédients: {stats['total_ingredients']}").pack(anchor='w', padx=20)
        ttk.Label(general_frame, text=f"Potions favorites: {stats['favorites']}").pack(anchor='w', padx=20)
        
        if stats['most_used_ingredient']:
            ing_id, count = stats['most_used_ingredient']
            ing_name = self.potion_manager.data["ingredients"][ing_id]["name"]
            ttk.Label(general_frame, text=f"Ingrédient le plus utilisé: {ing_name} ({count} fois)").pack(anchor='w', padx=20)
        
        # Onglet catégories
        categories_frame = ttk.Frame(notebook)
        notebook.add(categories_frame, text="Catégories")
        
        ttk.Label(categories_frame, text="Répartition par Catégorie", font=('Arial', 14, 'bold')).pack(pady=10)
        for category, count in stats['categories'].items():
            ttk.Label(categories_frame, text=f"{category}: {count} potions").pack(anchor='w', padx=20)
        
        # Onglet bases
        bases_frame = ttk.Frame(notebook)
        notebook.add(bases_frame, text="Bases")
        
        ttk.Label(bases_frame, text="Utilisation des Bases", font=('Arial', 14, 'bold')).pack(pady=10)
        for base_id, count in stats['bases_used'].items():
            base_name = self.potion_manager.data["bases"][base_id]["name"]
            ttk.Label(bases_frame, text=f"{base_name}: {count} potions").pack(anchor='w', padx=20)
    
    def _cleanup_data(self):
        """Nettoyer les données (supprimer les entrées orphelines)"""
        # Ici on pourrait implémenter un nettoyage des données corrompues
        messagebox.showinfo("Nettoyage", "Fonction de nettoyage non implémentée dans cette version.")
    
    def _show_help(self):
        """Afficher l'aide"""
        help_text = """
GUIDE D'UTILISATION - Générateur de Potions v2.0

CRÉATION DE POTIONS:
1. Sélectionnez une base de potion
2. Choisissez un ingrédient à effet positif
3. Choisissez un ingrédient à effet négatif
4. Cliquez sur "Créer Potion"

RACCOURCIS CLAVIER:
- Ctrl+N: Créer une potion
- Ctrl+R: Réinitialiser le formulaire
- Ctrl+S: Exporter en CSV
- F5: Actualiser l'affichage

FONCTIONNALITÉS:
- Recherche dans la liste des potions
- Tri par différents critères
- Filtrage par catégorie ou favorites
- Gestion des favoris et notes
- Export/Import de données
- Statistiques détaillées

ASTUCES:
- Double-cliquez sur une potion pour voir les détails
- Utilisez la recherche d'ingrédients pour trouver rapidement
- Marquez vos potions favorites avec l'étoile
- Gérez vos ingrédients via le menu "Ingrédients"
- Sauvegardez régulièrement vos données

GESTION DES INGRÉDIENTS:
- Ctrl+I: Ouvrir le gestionnaire d'ingrédients
- Créez, modifiez et supprimez des ingrédients
- Système de contraindications et synergies
- Import/Export d'ingrédients en JSON/CSV
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Guide d'utilisation")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(help_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _show_about(self):
        """Afficher les informations sur l'application"""
        about_text = """
Générateur de Potions Avancé
Version 2.0

Application de création et gestion de potions alchimiques
pour jeux de rôle et univers fantasy.

Fonctionnalités:
• Création de potions par combinaison d'ingrédients
• Gestion complète avec favoris et notes
• Recherche et filtrage avancés
• Export/Import de données
• Statistiques détaillées
• Interface moderne et intuitive

Développé avec Python et Tkinter
Architecture modulaire et extensible
"""
        messagebox.showinfo("À propos", about_text)
    
    def _on_closing(self):
        """Gestion de la fermeture de l'application"""
        # Sauvegarder automatiquement
        self.potion_manager.data_manager.save_data()
        self.root.destroy()
    
    def run(self):
        """Lancer l'application"""
        self.root.mainloop()

# ==================== DONNÉES INITIALES ====================

def create_sample_ingredients():
    """Créer des ingrédients d'exemple si le fichier est vide"""
    sample_ingredients = {
        "sauge": {
            "id": "sauge", "name": "Sauge", "effect": "Purification", "type": "positif",
            "quality": "Mineur", "duration": "Instantané", "rarity": "Commun",
            "description": "Herbe purificatrice commune", "contraindications": [], "synergies": []
        },
        "ortie": {
            "id": "ortie", "name": "Ortie", "effect": "Enchevêtrement", "type": "négatif",
            "quality": "Mineur", "duration": "1 minute", "rarity": "Commun",
            "description": "Plante urticante provoquant l'enchevêtrement", "contraindications": [], "synergies": []
        },
        "belladone": {
            "id": "belladone", "name": "Belladone", "effect": "Empoisonné", "type": "négatif",
            "quality": "Majeur", "duration": "Instantané", "rarity": "Rare",
            "description": "Plante toxique mortelle", "contraindications": [], "synergies": []
        },
        "lotus": {
            "id": "lotus", "name": "Lotus", "effect": "Charme / Séduction", "type": "positif",
            "quality": "Mineur", "duration": "1 minute", "rarity": "Commun",
            "description": "Fleur enchanteresse", "contraindications": [], "synergies": []
        },
        "mandragore": {
            "id": "mandragore", "name": "Mandragore", "effect": "Assommé Légendaire", "type": "négatif",
            "quality": "Légendaire", "duration": "Jusqu'à réveil", "rarity": "Légendaire",
            "description": "Racine légendaire aux pouvoirs endormants", "contraindications": [], "synergies": []
        }
    }
    return sample_ingredients

# ==================== POINT D'ENTRÉE ====================

def main():
    """Point d'entrée principal"""
    try:
        # Vérifier si les données de base existent
        data_manager = DataManager()
        
        # Debug: Afficher les informations de base
        print(f"Fichier de données: {data_manager.data_file}")
        print(f"Fichier existe: {data_manager.data_file.exists()}")
        print(f"Nombre d'ingrédients: {len(data_manager.data.get('ingredients', {}))}")
        
        if not data_manager.data["ingredients"]:
            print("ATTENTION: Aucun ingrédient trouvé, ajout d'échantillons...")
            # Ajouter des ingrédients d'exemple
            sample_ingredients = create_sample_ingredients()
            data_manager.data["ingredients"].update(sample_ingredients)
            data_manager.save_data()
            print(f"Ingrédients d'exemple ajoutés: {len(sample_ingredients)}")
        
        # Lancer l'application
        app = PotionGeneratorApp()
        app.run()
        
    except Exception as e:
        messagebox.showerror("Erreur fatale", f"Impossible de démarrer l'application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()