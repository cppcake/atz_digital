import {
    new_player,
    new_answer,
    player_to_answer_by_id,
    player_unanswer_by_id,
    mark_player_finished,
    clear,
    set_topic,
    set_statement,
    set_qrcode,
    hide_session_info,
    set_wifi_ssid,
    set_wifi_password,
    show_counter,
    set_counter,
} from "./visualizer.js"


let state;


// Start the visualizer once the page has fully loaded
document.addEventListener("DOMContentLoaded", () => async function()
{    
    try
    {
        const socket = new WebSocket("subscribe_change");

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data["type"])
            {
                case "vote": vote(data["data"]["remote_id"], data["data"]["color"]); break;
                case "jump_statement": reapply_state(); break;
                case "phase": phase(data["data"]["phase"]); break;
            }
        }    
    }
        
    catch (e)
    {
        console.error(e);
        alert("Verbindung zu einer Therapie-Session konnte nicht aufgebaut werden. Lade die Seite noch einmal neu, sobald die Therapie gestartet wurde.");
        return;
    }

    start_screen();

    try
    {
        await reapply_state();
    }

    catch
    {
        console.log("No Therapy in progress...");
    }
    
}());


function start_screen()
{
    clear();
    set_topic("Visualizer");
    set_statement("Warten auf Therapiebeginn...");
    set_qrcode("/web/imgs/qr.png");
    set_wifi_ssid("ATZ Digital");
    set_wifi_password("digitaletherapie");
    show_counter(false);
}


async function reapply_state()
{    
    state = await get_state();
    console.log(state);

    clear();

    if (state.phase == 1)
    {
        hide_session_info();
        set_counter(state.current_statement + 1, state.topic.statements.length);
        show_counter(true);

        set_statement(state.topic.statements[state.current_statement].content);
        set_topic(state.topic.content);

        for (const answer of state.topic.answers)
        {
            new_answer(answer.content, answer.color, answer.icon)
        }

        // Create Players
        for (const player of state.players)
        {
            new_player(player.name, player.id, player.icon);
            if (player.answers[state.current_statement] != "None" && state.delayed_answers)
            {
                mark_player_finished(player.id);
            }
        }
    
        // If delayed_answers is true and at least 1 one did not vote, return
        if (state.delayed_answers)
        {
            console.log("HEY!");
            for (const player of state.players)
            {
                const answer = player.answers[state.current_statement];
                if (answer == "None")
                {
                    return;
                }
            }
        }

        // Move the players
        for (const player of state.players)
        {
            const answer = player.answers[state.current_statement];

            if (answer && answer !== "None")
            {
                player_to_answer_by_id(player.id, answer);
            } 
        }
    }
}


async function get_state()
{
    const response = await fetch("/therapy/state");

    if (!response.ok)
    {
        throw new Error("Failed to fetch therapy state");
    }

    return await response.json();
}


let everyone_already_answered = [];

async function phase(n)
{   
    everyone_already_answered = [];

    if (n == 0)
    {
        start_screen();
    }
    
    await reapply_state();
}

function vote(player_id, answer_color)
{
    switch (state.delayed_answers) {
        case false:
            for (const player of state.players)
            {
                if (player.id == player_id)
                {
                    if (answer_color === "None")
                    {
                        player_unanswer_by_id(player_id);
                    }
                    else
                    {
                        player_to_answer_by_id(player_id, answer_color);
                    }
                    
                    player.answers[state.current_statement] = answer_color;
                }
            }
            break;
        case true:
            // Add the new answer and mark the players as finished
            for (const player of state.players)
            {
                if (player.id == player_id)
                {                    
                    player.answers[state.current_statement] = answer_color;
                    mark_player_finished(player.id);
                }
            }

            // If any player did not finish voting yet, return
            for (const player of state.players)
            {
                if (player.answers[state.current_statement] == "None")
                {
                    return;
                }
            }

            // If nobody moved yet, move everyone. Else move just the voting player.
            if (!everyone_already_answered.includes(state.current_statement))
            {
                for (const player of state.players)
                {
                    player_to_answer_by_id(player.id, player.answers[state.current_statement]);
                    everyone_already_answered.push(state.current_statement);
                }
            } else
            {
                for (const player of state.players)
                {
                    if (player.id == player_id)
                    {
                        player_to_answer_by_id(player_id, player.answers[state.current_statement]);
                    }
                }
            }
            break;
    }
}
