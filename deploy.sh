#!/bin/bash

# --- KONFIGURACE ---
MAIN_FILE="main.py"

cleanup_and_exit() {
    trap - SIGINT
    echo -e "\n\nBuenos retardes"
    rm -f "${MAIN_FILE}.tmp"
    kill -SIGINT $$ 2>/dev/null || exit 0
}
trap cleanup_and_exit SIGINT

# --- POMOCNÉ FUNKCE ---
ensure_fzf() {
    if ! command -v fzf &> /dev/null; then
        echo "fzf nebyl nalezen. Používám standardní textový vstup."
    fi
}

get_next_version() {
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0")
    VERSION_NUM=${LAST_TAG#v}
    BASE=$(echo $VERSION_NUM | cut -d. -f1)
    MINOR=$(echo $VERSION_NUM | cut -d. -f2)
    NEW_MINOR=$((MINOR + 1))
    echo "v$BASE.$NEW_MINOR"
}

get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

# --- MENU OPERACE ---
manage_tags() {
    if command -v fzf &> /dev/null; then
        SELECTED_TAG=$(git tag --sort=-v:refname | fzf --height 40% --reverse --header "Vyber tag ke SMAZÁNÍ:")
    else
        echo "Dostupné tagy (posledních 10):"
        git tag --sort=-v:refname | head -n 10
        read -p "Napiš název tagu ke smazání: " SELECTED_TAG < /dev/tty
    fi

    if [[ -n "$SELECTED_TAG" ]]; then
        read -p "Opravdu smazat $SELECTED_TAG lokálně i na origin? (y/n): " -n 1 -r < /dev/tty
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git tag -d "$SELECTED_TAG"
            git push origin --delete "$SELECTED_TAG" || echo "Tag na origin už neexistuje."
            echo "Tag $SELECTED_TAG byl odstraněn."
        fi
    else
        echo "Nic nebylo vybráno."
    fi
}

run_release() {
    BRANCH=$(get_current_branch)
    echo "Kontrola repozitáře (branch: $BRANCH)..."

    if [[ -n $(git status --porcelain -uno) ]]; then
        echo "------------------------------------------------"
        echo "CHYBA: Máš neuložené změny v sledovaných souborech!"
        git status -s
        echo "------------------------------------------------"
        echo "Udělej 'git commit' nebo 'git stash' a zkus to znovu."
        read -p "Stiskni [Enter] pro návrat do menu..." < /dev/tty
        return 1
    fi

    echo "Kontroluji syntaxi..."
    python3 -m py_compile main.py main_statistika.py main_grafy.py utils.py
    for f in statisticke_vypracovani/*/logic.py; do
        python3 -m py_compile "$f"
    done
    if [ $? -eq 0 ]; then
        echo "Syntaxe OK."
    else
        echo "Syntaxe je špatně, oprav to dřív, než uděláš tag!"
        read -p "Stiskni [Enter] pro návrat do menu..." < /dev/tty
        return 1
    fi

    NEW_TAG=$(get_next_version)
    echo "------------------------------------------------"
    echo "Připravuji release verze: $NEW_TAG"
    echo "Branch: $BRANCH"
    echo "------------------------------------------------"

    sed "s@CURRENT_VERSION = \".*\"@CURRENT_VERSION = \"$NEW_TAG\"@" "$MAIN_FILE" > "${MAIN_FILE}.tmp" && mv "${MAIN_FILE}.tmp" "$MAIN_FILE"

    read -p "Zadej poznámky k releasu (nebo Enter): " REL_NOTES < /dev/tty
    REL_NOTES=${REL_NOTES:-"Release $NEW_TAG"}

    git add "$MAIN_FILE"
    git commit -m "Release $NEW_TAG: $REL_NOTES"
    git tag -a "$NEW_TAG" -m "$REL_NOTES"

    echo "--- Pushuji do origin ($BRANCH + tag $NEW_TAG) ---"
    git push origin "$BRANCH" && git push origin "$NEW_TAG"

    echo ""
    echo "Hotovo! Verze $NEW_TAG je venku."
    echo "GitHub Actions teď buildí: statistika + grafy (Linux + Windows)"
    echo "Sleduj: https://github.com/matyas095/ZM2_Mereni/actions"
    read -p "Stiskni [Enter] pro návrat do menu..." < /dev/tty
}

run_local_build() {
    echo ""
    echo "--- Lokální build ---"

    if command -v fzf &> /dev/null; then
        BUILD_CHOICE=$(echo -e "1. Statistika (Linux)\n2. Grafy (Linux)\n3. Oba (Linux)\n4. Simulace release" | fzf --height 15% --reverse --header "Co buildnout?")
    else
        echo "1. Statistika (Linux)"
        echo "2. Grafy (Linux)"
        echo "3. Oba (Linux)"
        echo "4. Simulace release"
        read -p "Vyber (1-4): " BUILD_CHOICE < /dev/tty
    fi

    case "$BUILD_CHOICE" in
        *1*) bash builder/build_statistika_linux.sh ;;
        *2*) bash builder/build_grafy_linux.sh ;;
        *3*)
            bash builder/build_statistika_linux.sh
            bash builder/build_grafy_linux.sh
            ;;
        *4*)
            read -p "Verze pro simulaci (např. v0.3-test): " SIM_VER < /dev/tty
            SIM_VER=${SIM_VER:-"v0.0-test"}
            bash builder/simulate_release.sh "$SIM_VER"
            ;;
    esac

    read -p "Stiskni [Enter] pro návrat do menu..." < /dev/tty
}

# --- HLAVNÍ SMYČKA ---

ensure_fzf

while true; do
    clear
    echo -e "\n--- Deploy Management ---"
    echo "Branch: $(get_current_branch) | Poslední tag: $(git describe --tags --abbrev=0 2>/dev/null || echo 'žádný') | Další: $(get_next_version)"
    echo ""
    OPTIONS="1. Full Release (Tag + Push → CI build)\n2. Git Tag Management (Delete)\n3. Lokální build\n4. Exit"

    if command -v fzf &> /dev/null; then
        CHOICE=$(echo -e "$OPTIONS" | fzf --height 15% --reverse --header "Vyber akci:" --cycle --bind 'ctrl-c:abort')

        if [ $? -ne 0 ]; then
            cleanup_and_exit
        fi
    else
        echo -e "$OPTIONS"
        read -p "Vyber (1-4): " CHOICE < /dev/tty
    fi

    [[ -z "$CHOICE" ]] && continue

    case "$CHOICE" in
        *1*) run_release ;;
        *2*)
            manage_tags
            read -p "Hotovo. Stiskni [Enter]..." < /dev/tty
            ;;
        *3*) run_local_build ;;
        *4* | "Exit")
            cleanup_and_exit
            ;;
    esac
done
