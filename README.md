# Gestion des interventions Fibre Optique

Version 1 — application locale pour Kali Linux.

## Installation
```bash
cd gestion_fibre_optique
chmod +x launch.sh
./launch.sh
```

Puis ouvrir Firefox sur l'adresse indiquée par Streamlit (généralement http://localhost:8511).

## Principe
Une nouvelle intervention est ajoutée chaque jour avec un numéro unique `INT-AAAA-XXXX`.
La base SQLite `data/fibre.db` conserve l'historique.
Les photos sont stockées dans `uploads/NUMERO_INTERVENTION/`.

## Évolutions prévues
- génération de rapports PDF professionnels ;
- signature/validation ;
- mesures OTDR détaillées ;
- inventaire matériel ;
- fiches clients/sites ;
- historique des pannes par site ;
- sauvegarde/restauration ;
- tableau de bord mensuel.
