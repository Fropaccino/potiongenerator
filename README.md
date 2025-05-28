Mode d’emploi du Générateur de Potions – Équipe d’Animation
Le logiciel permet de générer, consulter et exporter toutes les potions créées en jeu. Voici comment l’utiliser correctement.


IMPORTANT: Mise à jour du fichier JSON

Il est essentiel de télécharger le dossier DATA et le fichier potions_data.json à jour depuis le Google Drive avant chaque événement, puis de le re-téléverser à la fin de l'événement. Ce fichier contient l’ensemble des ingrédients disponibles et des potions déjà créées.
Si cette étape est oubliée, le logiciel risque de fonctionner avec une version incomplète, entraînant des manques d’ingrédients ou des doublons de potions.
C’est ce fichier qui assure la continuité et la cohérence du système d’alchimie entre chaque édition.

1. Structure d'une potion
Chaque potion est composée de :
Une base (Eau, Huile, Pâte, Vin alchimique, Cendre)


Un ingrédient à effet positif


Un ingrédient à effet négatif


Ces trois éléments doivent être sélectionnés pour générer une potion.

2.  Générer une potion
Choisissez une base dans la première liste déroulante.


Choisissez un ingrédient positif (liste filtrée automatiquement).


Choisissez un ingrédient négatif.


Si la combinaison est valide et non utilisée, le bouton Générer Potion devient actif.


Cliquez pour créer la potion. Elle sera :


Automatiquement nommée (Potion Mineur de Guérison et Poison)


Classée selon la qualité des ingrédients


Ajoutée à la base de données interne


Si la combinaison a déjà été utilisée, le bouton sera désactivé et un message vous avertira du doublon.



3. Consulter les potions
À droite de l’écran, la liste des potions générées s’affiche.


Vous pouvez trier par Nom ou Catégorie.


En cliquant sur une potion, ses détails s’affichent :


Base


Ingrédients


Effets


Durées


Qualités



4. Exporter/Importer les potions
Utilisez le bouton Exporter/Importer en CSV pour générer un fichier Excel contenant toutes les potions.


Fichier compatible avec Excel, Google Sheets ou LibreOffice.


Les accents sont pris en charge (format UTF-8-sig).



5. Gestion des ingrédients
Cliquez sur Ajouter un ingrédient pour en créer un nouveau (nom, effet, type, qualité, durée).


Cliquez sur Modifier un ingrédient pour éditer les informations d’un ingrédient existant.


⚠️ Un ingrédient ne peut pas avoir à la fois un effet positif et négatif. Utilisez le bon type.

6. Sécurité et cohérence
Le logiciel empêche les doublons


Les recettes sont sauvegardées automatiquement


Le bouton Générer est désactivé tant que la combinaison n’est pas valide




