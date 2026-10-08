# This rcfile belongs only to the shared workshop shell, not nested shells.
[[ -f ~/.bashrc ]] && source ~/.bashrc

WORKSHOP_RUN_DIR=${WORKSHOP_RUN_DIR:-/tmp/workshop-terminal}
mkdir -p "$WORKSHOP_RUN_DIR"
chmod 700 "$WORKSHOP_RUN_DIR"
tmux set-option -p -t "$TMUX_PANE" @workshop_shell_pid "$BASHPID"

_workshop_busy() {
    tmux set-option -p -t "$TMUX_PANE" @workshop_ready 0
}

_workshop_prompt() {
    tmux set-option -p -t "$TMUX_PANE" @workshop_ready 1
}

_workshop_accept_run() {
    [[ -f "$WORKSHOP_RUN_DIR/command" ]] || return
    if [[ -n "$READLINE_LINE" ]]; then
        printf 'busy\n' > "$WORKSHOP_RUN_DIR/result"
        return
    fi
    local command
    IFS= read -r -d '' command < "$WORKSHOP_RUN_DIR/command" || true
    rm -f "$WORKSHOP_RUN_DIR/command"
    READLINE_LINE=$command
    READLINE_POINT=${#READLINE_LINE}
    _workshop_busy
    # Queue Enter only after readline has accepted the command at an empty
    # prompt. Output and command echo remain in the same visible tmux pane.
    tmux send-keys -t "$TMUX_PANE" Enter
    printf 'sent\n' > "$WORKSHOP_RUN_DIR/result"
}

# Clearing readiness before Enter also covers incomplete quotes and PS2 prompts,
# where Bash has not executed anything and the foreground process is still Bash.
bind -x '"\C-x\C-b":_workshop_busy'
bind '"\C-x\C-a": accept-line'
bind '"\C-m": "\C-x\C-b\C-x\C-a"'
bind '"\C-j": "\C-x\C-b\C-x\C-a"'
bind -x '"\e[99~":_workshop_accept_run'
trap '[[ $BASH_COMMAND == _workshop_accept_run ]] || _workshop_busy' DEBUG
PROMPT_COMMAND=_workshop_prompt
