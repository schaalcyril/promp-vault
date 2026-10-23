# Progression, annulation et performances

## Mise en œuvre

L’interface utilise POST /api/analyze-stream (NDJSON). Chaque analyse tourne dans un processus isolé créé par un forkserver Linux préchargé ; aucun fork du processus ASGI multithreadé. Le calcul est terminé lors de la déconnexion du client, à la fin du traitement ou au dépassement de la limite de dix minutes. Une seule analyse simultanée par instance ; les requêtes supplémentaires sont refusées avec 429 plutôt que conservées en file.

La progression indique les étapes et le nombre de blocs traités, pas le temps restant. Le résultat est communiqué uniquement à la fin. Le navigateur prépare les remplacements dans un Web Worker annulable. Aucun travail ni résultat n’est persisté.

La route historique /api/analyze est conservée pour les tests et la compatibilité ; elle ne fournit pas ces garanties d’annulation. Le frontend utilise exclusivement la route avec flux.

## Vérifications

31 tests backend et 2 tests frontend réussis. Corpus qualité : 32/32 correspondances exactes, sans régression sur les 30 scénarios synthétiques connus. Compilation TypeScript/Vite réussie. Progression, résultat via Web Worker et annulation vérifiés dans le navigateur sur un exemple et environ 133 Kio. Une mesure HTTP via nginx confirme la libération du traitement après déconnexion : la petite analyse suivante se termine en 0,127 seconde après la fermeture du flux.

## Protocole des mesures

Poste Ubuntu i7-6820HQ, environ 16 Go de RAM. Docker, limite 4 Gio, réseau désactivé pour les benchmarks moteur. Corpus de logs ASCII répétitifs, avec un secret et une IP en préfixe, peu de détections. Modèles préchargés. Une mesure par volume, pas une distribution statistique. Le poste a aussi servi aux compilations/tests pendant cette session : mesures indicatives, pas un benchmark isolé. Les pics RSS concernent le processus évalué, pas l’ensemble des processus du service. Le service au repos utilise environ 584 Mio selon Docker après préchargement.

Le benchmark JS sous Node traite 10 Mio et 374 492 occurrences en 0,87 s, pic RSS 287 Mio. Il ne mesure ni les transferts Web Worker ni la réactivité ou la mémoire du navigateur. Un test complet navigateur à 10 Mio reste à réaliser.

## Limites

La taille maximale acceptée ne constitue pas une promesse de rapidité. Les logs très denses en entités, lignes uniques, textes FR/EN mixtes et contenus malformés peuvent produire des performances différentes. La revue reste limitée aux 300 premières détections dans ce prototype. Le moteur effectue encore deux passages NLP par bloc ; la réutilisation des résultats linguistiques est une piste de travail, à tester sans réduction de couverture.

## Résultats moteur

| Volume | Durée | Pic RSS | Résultat |
|---|---:|---:|---|
| 64 Kio | 3.93 s | 366.4 Mio | Terminé |
| 1 Mio | 62.32 s | 368.0 Mio | Terminé |
| 10 Mio | 300.0 s | 377.9 Mio | Interrompu à 300 s, résultat non disponible |

La cible de 10 Mio reste non validée en termes de performance. Priorité suivante : profiler les détecteurs, supprimer les doubles calculs NLP et rejouer le corpus de qualité avant toute nouvelle mesure.
