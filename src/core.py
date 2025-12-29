"""
Core module for task management.

Ce module contient la logique métier principale pour la gestion des tâches.
Il fournit les fonctions de base pour créer, modifier, supprimer et afficher des tâches.

Format des tâches: Chaque tâche est stockée sous forme "ID;Description;étiquette1,étiquette2" 
ou "ID;Description;None" (pour les tâches sans étiquettes) dans le fichier.

Rétrocompatibilité: Supporte aussi l'ancien format "ID;Description" (sans étiquettes).
"""


def parse_tasks(tasks):
    """
    Parse les lignes brutes du fichier en une liste structurée de tâches.
    
    Args:
        tasks (list): Liste des lignes lues depuis le fichier de tâches
        
    Returns:
        list: Liste de tuples (id: int, description: str, labels: list[str], status: str, dependence: int|None) 
              représentant les tâches. Si pas d'étiquettes, labels=[]. Si pas de dépendance, dependence=None.
        
    Note:
        - Ignore les lignes vides
        - Ignore les lignes mal formatées (sans ';' ou avec ID non numérique)
        - Le format attendu est "ID;Description;Labels;Status;Dependence"
        - Gère la rétrocompatibilité avec les anciens formats
        
    Exemple:
        >>> parse_tasks(["1;Faire les courses;None;suspended;None", "2;Réviser;Urgent;started;1"])
        [(1, 'Faire les courses', [], 'suspended', None), (2, 'Réviser', ['Urgent'], 'started', 1)]
    """
    
    parsed_tasks = []
    for line in tasks:
        line = line.strip()
        if line:  # Ignore les lignes vides
            parts = line.split(";")
            if len(parts) >= 2:  # Au minimum ID et description
                try:
                    tid = int(parts[0])
                    description = parts[1]
                    # Gestion des étiquettes (rétrocompatibilité)
                    if len(parts) >= 3 and parts[2] != "None":
                        labels = [label.strip() for label in parts[2].split(",") if label.strip()]
                    else:
                        labels = []

                    # Gestion statut
                    if len(parts) >= 4 and parts[3].strip():
                        status = parts[3].strip()
                    else:
                        status = "suspended"

                    # Dépendances
                    if len(parts) >= 5 and parts[4].strip().isdigit():
                        dependence = int(parts[4].strip())
                    else:
                        dependence = None
                    
                    parsed_tasks.append((tid, description, labels, status, dependence))
                except ValueError:
                    # Ignore les lignes avec un ID non numérique
                    continue

    return parsed_tasks


def add(tasks, details, labels = None, status="suspended"):
    """
    Ajoute une nouvelle tâche avec un ID auto-incrémenté.
    
    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        details (str): Description de la nouvelle tâche
        labels (list[str], optional): Liste d'étiquette(s) de la nouvelle tâche, None si aucune
        status (str, optional): Statut initial de la tâche (défaut: "suspended")
        
    Returns:
        tuple: (new_id: int, description: str, labels: list, task_line: str) ou (None, None, None, None) si annulé
            - new_id: L'ID assigné à la nouvelle tâche
            - description: La description de la tâche
            - labels: Liste des étiquettes, vide si aucune
            - task_line: La ligne formatée à écrire dans le fichier (format: ID;Description;Labels;Status;Dependence)
            
    Note:
        - L'ID est calculé comme max(IDs existants) + 1
        - Si aucune tâche n'existe, l'ID commence à 1
        - L'utilisateur peut définir une dépendance de manière interactive
        - La ligne retournée inclut le saut de ligne final
        - Retourne (None, None, None, None) si l'utilisateur annule (Ctrl+C)
        
    Example:
        >>> add(["1;Tâche existante;None;completed;None"], "Nouvelle tâche", ["urgent"], "suspended")
        (2, 'Nouvelle tâche', ['urgent'], '2;Nouvelle tâche;urgent;suspended;None\n')
    """

    # Trouve le prochain ID disponible en analysant les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    if parsed_tasks:
        # Calcule l'ID maximum et ajoute 1
        new_id = max(task[0] for task in parsed_tasks) + 1
    else:
        # Premier ID si aucune tâche n'existe
        new_id = 1

    # Réécriture de labels
    if labels == None:
        labels_list = []
    else:
        labels_list = labels
    
    labels_str = ",".join(labels_list) if labels_list else "None"
    
    # Vérification du statut
    if status not in ["started", "suspended", "completed", "cancelled"]:
        print(f"Statut '{status}' invalide, utilisation de 'suspended' à la place.")
        status = "suspended"
    print(f"Statut de la nouvelle tâche : {status}")

    # Gestion des dépendances
    id_dep = None
    if parsed_tasks:
        try:
            dependence = input("Cette tâche dépend t-elle d'une autre tâche ? O/N : ")
            while dependence.lower() not in ["o", "n", "oui", "non"]:
                dependence = input("Input invalide, cette tâche dépend t-elle d'une autre tâche ? O/N : ")

            if dependence.lower() in ["oui", "o"]:
                print("Liste des tâches existantes :")
                id_list = []
                for (tid, desc, _, state, _) in parsed_tasks:
                    print(f"{tid}: {desc} ({state})")
                    id_list.append(tid)

                while True:
                    try:
                        id_dep = int(input("Laquelle ? "))
                        if id_dep in id_list:
                            if status == "started" or status == "completed":
                                # On cherche le statut de la tâche dépendante
                                parent_status = "suspended"
                                for (pid, _, _, pstate, _) in parsed_tasks:
                                    if pid == id_dep:
                                        parent_status = pstate
                                        break
                            
                                if parent_status != "completed":
                                    print(f"La tâche dépendante n'est pas complétée (statut actuel : {parent_status}). La nouvelle tâche sera mise en 'suspended'.")
                                    status = "suspended"
                            break
                        else:
                            print(f"Cette tâche n'existe pas, entrez un identifiant valide")
                    except ValueError:
                        print("Erreur : veuillez entrer un nombre valide")
        except KeyboardInterrupt:
            print("\nOpération annulée")
            return None, None, None, None

    # Formate la ligne pour l'écriture dans le fichier
    new_task_line = f"{new_id};{details};{labels_str};{status};{id_dep}\n"
    return (new_id, details, labels_list, new_task_line)


def modify(tasks, task_id, new_details = None, new_status = None):
    """
    Modifie la description et/ou le statut d'une tâche existante par son ID.
    
    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à modifier
        new_details (str, optional): Nouvelle description pour la tâche
        new_status (str, optional): Nouveau statut pour la tâche (started, suspended, completed, cancelled)
        
    Returns:
        tuple: (found: bool, updated_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et modifiée, False sinon
            - updated_tasks: Liste des tâches mises à jour (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à l'ancienne tâche
            
    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Si l'ID n'est pas numérique, retourne (False, [], None)
        - Vérifie les dépendances avant de permettre le passage au statut "started"
        - La liste retournée contient toutes les tâches, modifiée incluse
        
    Example:
        >>> modify(["1;Ancienne tâche;None;suspended;None"], "1", "Nouvelle description", "started")
        (True, [(1, 'Nouvelle description', [], 'started', None)], (1, 'Ancienne tâche', [], 'suspended', None))
    """

    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        # ID invalide (non numérique)
        return False, [], None
        
    # Parse les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    found = False
    old_task = None

    # Recherche et modification de la tâche correspondante
    for i, (tid, desc, lab, state, dep) in enumerate(parsed_tasks):
        if tid == task_id:
            # IMPORTANT : On sauvegarde l'ancienne tâche AVANT toute modification
            old_task = (tid, desc, lab, state, dep)
            
            # 1. Mise à jour du statut avec vérification des dépendances
            if new_status is not None:
                # Si on essaie de DÉMARRER une tâche qui a une dépendance
                if new_status == "started" and dep is not None:
                    # On vérifie si la tâche parente est terminée
                    parent_completed = False
                    parent_exists = False

                    for (pid, _, _, pstate, _) in parsed_tasks:
                        if pid == dep:
                            parent_exists = True
                            if pstate == "completed":
                                parent_completed = True
                            break
                    
                    if parent_exists and not parent_completed:
                        print(f"REFUSÉ : La tâche parente (ID {dep}) n'est pas terminée.")
                        # On ne modifie pas 'state', il reste l'ancien
                    else:
                        state = new_status

                # Si c'est un autre statut valide ou s'il n'y a pas de dépendance
                elif new_status in ["started", "suspended", "completed", "cancelled"]:
                    state = new_status
                
                else:
                    print(f"Statut '{new_status}' invalide, pas de modification.")

            # 2. Mise à jour de la description
            if new_details is not None:
                desc = new_details
                
            # On met à jour la ligne dans la liste
            parsed_tasks[i] = (tid, desc, lab, state, dep)
            found = True
            break    
    
    return found, parsed_tasks, old_task
    
def rm(tasks, task_id):
    """
    Supprime une tâche par son ID et met à jour les dépendances.
    
    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à supprimer
        
    Returns:
        tuple: (found: bool, remaining_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et supprimée, False sinon
            - remaining_tasks: Liste des tâches restantes (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à la tâche supprimée
            
    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Si l'ID n'est pas numérique, retourne (False, tâches_originales, None)
        - Les IDs des autres tâches ne sont pas réassignés
        - Les dépendances vers la tâche supprimée sont automatiquement retirées
        
    Example:
        >>> rm(["1;Tâche 1;None;completed;None", "2;Tâche 2;None;suspended;1"], "1")
        (True, [(2, 'Tâche 2', [], 'suspended', None)], (1, 'Tâche 1', [], 'completed', None))
    """

    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        # ID invalide, retourne les tâches non modifiées
        return False, parse_tasks(tasks), None
        
    # Parse les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    original_length = len(parsed_tasks)
    
    # Filtre les tâches pour enlever celle avec l'ID spécifié
    filtered_tasks = []
    for (tid, desc, lab, status, dep) in parsed_tasks:  
        if tid != task_id:
            filtered_tasks.append((tid, desc, lab, status, dep))
        else:
            old_task = (tid, desc, lab, status, dep)
    
    # Détermine si une tâche a été supprimée
    found = len(filtered_tasks) < original_length

    final_tasks = []

    if found:
        # Met à jour les dépendances des autres tâches
        for (tid, desc, lab, status, dep) in filtered_tasks:
            if dep == task_id:
                final_tasks.append((tid, desc, lab, status, None))
            else:
                final_tasks.append((tid, desc, lab, status, dep))
    else:
        final_tasks = filtered_tasks
        old_task = None

    return found, filtered_tasks, old_task
            
def add_options(tasks, task_id, labels=None, id_dep=None):
    """
    Ajoute une ou plusieurs étiquette(s) et/ou dépendance à une tâche existante.

    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à modifier
        labels (list[str], optional): Liste d'étiquette(s) à ajouter (évite les doublons)
        id_dep (int, optional): ID de la tâche dont dépend la tâche cible

    Returns:
        tuple: (found: bool, updated_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et modifiée, False sinon
            - updated_tasks: Liste des tâches mises à jour (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à l'ancienne tâche
            
    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Les étiquettes en doublon sont automatiquement ignorées
        - Si une dépendance existe déjà, demande confirmation à l'utilisateur
        - Si l'ID n'est pas numérique, retourne (False, [], None)
    """

    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        return False, [], None

    parsed_tasks = parse_tasks(tasks)
    found = False
    old_task = None

    for i, (tid, desc, lab, state, dep) in enumerate(parsed_tasks):
        if tid == task_id:
            old_task = (tid, desc, lab, state, dep)

            # Mise à jour des étiquettes
            if labels is not None:
                new_lab = lab[:] if lab else []
                for label in labels:
                    if label not in new_lab:
                        new_lab.append(label)
            else:
                new_lab = lab

            # Mise à jour de la dépendance
            if id_dep is not None:
                if dep is not None:
                    # Demande à l'utilisateur s'il veut modifier la dépendance
                    print(f"Tâche {tid} dépend déjà de la tâche {dep}.")
                    modify_dep = input("Voulez-vous modifier la dépendance ? (O/N) : ").lower()
                    while modify_dep not in ["o", "n", "oui", "non"]:
                        modify_dep = input("Réponse invalide, voulez-vous modifier la dépendance ? (O/N) : ").lower()
                    if modify_dep in ["o", "oui"]:
                        dep = id_dep
                else:
                    dep = id_dep

            parsed_tasks[i] = (tid, desc, new_lab, state, dep)
            found = True
            break

    return found, parsed_tasks, old_task

def rmLabel(tasks, task_id):
    """
    Supprime une étiquette d'une tâche existante en demandant à l'utilisateur quelle étiquette supprimer.

    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à modifier

    Returns:
        tuple: (found: bool, updated_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et modifiée, False sinon
            - updated_tasks: Liste des tâches mises à jour (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à l'ancienne tâche
            
    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Si l'ID n'est pas numérique, retourne (False, [], None)
        - Demande interactivement à l'utilisateur quelle étiquette supprimer
        - Gère la validation robuste de l'entrée utilisateur
        - Retourne (False, parsed_tasks, None) si l'utilisateur annule (Ctrl+C)
        
    Example:
        >>> rmLabel(["1;Tâche 1;None;suspended;None", "2;Tâche 2;tag1,tag2;started;None"], "2")
        # Affiche: 0: tag1, 1: tag2
        # Utilisateur entre: 0
        (True, [(1, 'Tâche 1', [], 'suspended', None), (2, 'Tâche 2', ['tag2'], 'started', None)], (2, 'Tâche 2', ['tag1', 'tag2'], 'started', None))
    """
    
    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        # ID invalide (non numérique)
        return False, [], None
        
    # Parse les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    found = False
    
    # Recherche et modification de la tâche correspondante
    for i, (tid, desc, lab, status, dep) in enumerate(parsed_tasks):
        if tid == task_id:
            old_task = (tid, desc, lab[:], status, dep)
            if lab:
                print("Étiquettes de la tâche :")
                for j, label in enumerate(lab):
                    print(f"{j}: {label}")
                
                # Validation robuste de l'entrée utilisateur
                while True:
                    try:
                        n = int(input("Entrez le numéro de l'étiquette à supprimer : "))
                        if 0 <= n < len(lab):
                            break
                        else:
                            print(f"Le numéro doit être entre 0 et {len(lab)-1}")
                    except ValueError:
                        print("Erreur : veuillez entrer un nombre valide")
                    except KeyboardInterrupt:
                        print("\nOpération annulée")
                        return False, parsed_tasks, None
            
                # Suppression de l'étiquette
                lab.pop(n)
                parsed_tasks[i] = (tid, desc, lab, status, dep)
            else:
                print("Cette tâche n'a pas d'étiquettes à supprimer")
            found = True
            break
    
    return found, parsed_tasks, old_task


def clearLabel(tasks, task_id):
    """
    Supprime l'ensemble des étiquettes d'une tâche en utilisant son ID.

    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à modifier

    Returns:
        tuple: (found: bool, updated_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et modifiée, False sinon
            - updated_tasks: Liste des tâches mises à jour (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à l'ancienne tâche

    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Si l'ID n'est pas numérique, retourne (False, [], None)
        
    Example:
        >>> clearLabel(["1;Tâche 1;None;suspended;None", "2;Tâche 2;tag1,tag2;started;None"], "2")
        (True, [(1, 'Tâche 1', [], 'suspended', None), (2, 'Tâche 2', [], 'started', None)], (2, 'Tâche 2', ['tag1', 'tag2'], 'started', None))
    """
    
    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        # ID invalide (non numérique)
        return False, [], None
        
    # Parse les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    found = False
    
    # Recherche et modification de la tâche correspondante
    for i, (tid, desc, lab, status, dep) in enumerate(parsed_tasks):
        if tid == task_id:
            old_task = (tid, desc, lab, status, dep)
            parsed_tasks[i] = (tid, desc, [], status, dep)
            found = True
            break
    
    return found, parsed_tasks, old_task

def rmDep(tasks, task_id):
    """
    Supprime la dépendance associée à une tâche en utilisant son ID.

    Args:
        tasks (list): Liste des lignes existantes du fichier de tâches
        task_id (str|int): ID de la tâche à modifier

    Returns:
        tuple: (found: bool, updated_tasks: list, old_task: tuple)
            - found: True si la tâche a été trouvée et modifiée, False sinon
            - updated_tasks: Liste des tâches mises à jour (tuples à 5 éléments)
            - old_task: Tuple (id, desc, lab, status, dep) correspondant à l'ancienne tâche avant suppression

    Note:
        - L'ID peut être fourni comme string ou int, il sera converti
        - Si l'ID n'est pas numérique, retourne (False, [], None)
        
    Example:
        >>> rmDep(["1;Tâche 1;None;completed;None", "2;Tâche 2;tag1;suspended;1"], "2")
        (True, [(1, 'Tâche 1', [], 'completed', None), (2, 'Tâche 2', ['tag1'], 'suspended', None)], (2, 'Tâche 2', ['tag1'], 'suspended', 1))
    """

    # Validation et conversion de l'ID
    try:
        task_id = int(task_id)
    except ValueError:
        # ID invalide (non numérique)
        return False, [], None
        
    # Parse les tâches existantes
    parsed_tasks = parse_tasks(tasks)
    found = False
    
    # Recherche et modification de la tâche correspondante
    for i, (tid, desc, lab, state, dep) in enumerate(parsed_tasks):
        if tid == task_id:
            old_task = (tid, desc, lab, state, dep)
            parsed_tasks[i] = (tid, desc, lab, state, None)
            found = True
            break
    
    return found, parsed_tasks, old_task

def show(tasks):
    """
    Affiche la liste des tâches dans un tableau formaté, triées par ID.
    
    Args:
        tasks (list): Liste des lignes du fichier de tâches
        
    Returns:
        None: Affiche directement le résultat sur stdout
        
    Note:
        - Affiche "No tasks found." si aucune tâche n'existe
        - Le tableau s'adapte automatiquement à la longueur des colonnes
        - Les tâches sont automatiquement triées par ID croissant
        - Format du tableau avec 5 colonnes: id, description, étiquette(s), statut, dépendance
                           
    Example:
        >>> show(["2;Seconde tâche;None;suspended;None", "1;Première tâche;tag1,tag2;started;2"])
        +-----+-----------------+----------------+----------+------------+
        | id  | description     | étiquette(s)   | statut   | dépendance |
        +-----+-----------------+----------------+----------+------------+
        | 1   | Première tâche  | tag1, tag2     | started  | 2          |
        | 2   | Seconde tâche   | None           | suspended| None       |
        +-----+-----------------+----------------+----------+------------+
    """

    # Parse et vérifie s'il y a des tâches
    parsed_tasks = parse_tasks(tasks)
    if not parsed_tasks:
        print("No tasks found.")
        return
    
    # Trie les tâches par ID croissant
    sorted_tasks = sorted(parsed_tasks, key=lambda x: x[0])
    
    # Calcule la largeur optimale pour la colonne description
    max_desc_length = max(len(desc) for _, desc, _, _, _ in sorted_tasks) if sorted_tasks else 10
    max_desc_length = max(max_desc_length, 11)  # Largeur minimale pour "description"
    
    # Calcule la largeur optimale pour la colonne étiquette(s)
    max_lab_length = max(len(", ".join(lab)) for _, _, lab, _, _ in sorted_tasks) if sorted_tasks else 11
    max_lab_length = max(max_lab_length, 12)  # Largeur minimale pour "étiquette(s)"

    # Largeur dynamique pour état et dépendance
    max_state_length = max(len(state) for _, _, _, state, _ in sorted_tasks) if sorted_tasks else 6
    max_state_length = max(max_state_length, 6)  # Largeur minimale

    max_dep_length = max(len(str(dep)) if dep else 4 for _, _, _, _, dep in sorted_tasks) if sorted_tasks else 4
    max_dep_length = max(max_dep_length, 10)  # Largeur minimale

    # Construction du tableau
    border_line = f"+-----+{'-' * (max_desc_length + 2)}+{'-' * (max_lab_length + 2)}+{'-' * (max_state_length + 2)}+{'-' * (max_dep_length + 2)}+"
    header_line = f"| {'id':<3} | {'description':<{max_desc_length}} | {'étiquette(s)':<{max_lab_length}} | {'statut':<{max_state_length}} | {'dépendance':<{max_dep_length}} |"

    print(border_line)
    print(header_line)
    print(border_line)
    
    # Affichage de chaque tâche
    for task_id, description, labels, state, dep in sorted_tasks:
        labels_str = ", ".join(labels) if labels else "None"
        print(f"| {task_id:<3} | {description:<{max_desc_length}} | {labels_str:<{max_lab_length}} | {state:<{max_state_length}} | {dep if dep else 'None':<{max_dep_length}} |")

    print(border_line)