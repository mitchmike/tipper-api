$(document).ready(function () {
    teamTableUpdate(false)
    oppTableUpdate(false)
    hideExtraRows()
})

function toggleCheckBox(classname, checked) {
    const checkboxes = document.getElementsByClassName(classname)
    for (const checkbox of checkboxes) {
        checkbox.checked = checked
        console.log(checkbox)
    }
}
document.getElementById("selectAllBtn").addEventListener('click', () => {
    toggleCheckBox('feature-check', true)
})
document.getElementById("selectNoneBtn").addEventListener('click', () => {
    toggleCheckBox('feature-check', false)
})

const selectGamesBtn = document.getElementById("selectGamesBtn")
const selectAllRoundsBtn = document.getElementById("selectAllRoundsBtn")
const selectNoneRoundsBtn = document.getElementById("selectNoneRoundsBtn")
selectGamesBtn.addEventListener('click', function () {
    const hidden = year_round_table.hidden
    year_round_table.hidden = !hidden
    selectAllRoundsBtn.hidden = !hidden
    selectNoneRoundsBtn.hidden = !hidden
})
selectAllRoundsBtn.addEventListener('click', function () {
    team_year_rounds = recent_year_rounds
    opp_year_rounds = recent_year_rounds
    teamTableUpdate()
    oppTableUpdate()
})
selectNoneRoundsBtn.addEventListener('click', function () {
    team_year_rounds = []
    opp_year_rounds = []
    teamTableUpdate()
    oppTableUpdate()
})
const game_count = document.getElementById("gameCountSelect")
game_count.addEventListener('change', function () {
    teamTableUpdate()
    oppTableUpdate()
    hideExtraRows()
})
const year_round_table = document.getElementById("year_round_table")
const teamselect = document.getElementById("teamselect")
teamselect.addEventListener('change', function () {
    teamTableUpdate()
    hideExtraRows()
})
const oppselect = document.getElementById("opponentselect")
oppselect.addEventListener('change', function () {
    oppTableUpdate()
    hideExtraRows()
})

const noTeamSelectedWarning = document.getElementById("noTeamSelectedWarning")

function teamTableUpdate(ignoreSelected = true) {
    team = teamselect.value
    tableUpdate(team, year_round_table, team_year_rounds, "team_year_rounds", 0, ignoreSelected)
}

function oppTableUpdate(ignoreSelected = true) {
    opp = oppselect.value
    tableUpdate(opp, year_round_table, opp_year_rounds, "opp_year_rounds", 7, ignoreSelected)
}

function hideExtraRows() {
    const trs = year_round_table.getElementsByTagName("tr")
    let rounds_available = !(teamselect.value === '' && oppselect.value === '')
    noTeamSelectedWarning.hidden = rounds_available
    if (!rounds_available) {
        for (let i = 2; i < trs.length; i++) {
            trs[i].hidden = true
        }
    } else {
        for (let i = 2; i < trs.length; i++) {
            if (i > (parseInt(game_count.value) + 1)) {
                trs[i].hidden = true
            } else {
                trs[i].hidden = false
            }
        }
    }
}

function tableUpdate(team, table, selected_y_rs, label, start_td_index, ignoreSelected) {
    const COLS = 6
    if (team === "") {
        return
    }
    team_games_url = `${team_games_url_root}?team=${team}&game_count=${game_count.value}`
    fetch(team_games_url)
        .then(response => response.json())
        .then(data => {
            let trs = table.getElementsByTagName('tr')
            // clear data
            for (let i = 2; i < trs.length; i++) {
                const tr = trs[i]
                const tds = tr.getElementsByTagName("td")
                for (let j = start_td_index; j < start_td_index + COLS; j++) {
                    tds[j].innerHTML = ""
                }
            }
            for (i = 0; i < data.length; i++) {
                const tr = trs[i + 2]  // +1 for header row and warning row
                let row = data[i]

                const y_r = [row.year, row.round_number]
                let checked = ""
                if (row.opponent != null) {
                    for (let j = 0; j < selected_y_rs.length; j++) {
                        if (arrayEquals(selected_y_rs[j], y_r) || ignoreSelected) {
                            checked = "checked"
                            break
                        }
                    }
                }
                const checkbox = `<div class="checkbox-wrapper-31" >
                                          <input class="round-check" ${checked} name="${label}" value="${y_r}" id="${label}_${y_r}" type="checkbox"/>
                                          <svg viewBox="0 0 35.6 35.6">
                                            <circle class="background round-check" cx="17.8" cy="17.8" r="17.8"></circle>
                                            <circle class="stroke" cx="17.8" cy="17.8" r="14.37"></circle>
                                            <polyline class="check" points="11.78 18.12 15.55 22.23 25.17 12.87"></polyline>
                                          </svg>
                                        </div>`


                const opponent = row.opponent != null ? team_map[row.opponent] : "No Game"
                const venue = row.venue != null ? row.venue : ""
                const winner = row.winner != null ? team_map[row.winner] : ""

                const tds = tr.getElementsByTagName('td')
                let k = 0
                for (let item of [checkbox, row.year, row.round_number, opponent, venue, winner]) {
                    tds[k + start_td_index].innerHTML = item
                    k++
                }
            }
        })
}

function arrayEquals(a, b) {
    return Array.isArray(a) &&
        Array.isArray(b) &&
        a.length === b.length &&
        a.every((val, index) => val === b[index]);
}