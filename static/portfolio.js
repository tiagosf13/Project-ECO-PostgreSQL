function loadUserData(id) {    
    // Load user data from file
    const userId = id; // Replace with user ID
    console.log(userId);
    const userFile = `/data/${userId}`;
    console.log(userFile)
    fetch(userFile).then(response => response.json()).then(userData => {
            // Define the coins and their values
            console.log(userData);
            const coins = userData.coins;

            // Define the number of each coin owned and sort by value
            const coinAmounts = userData.coinAmounts;
            const sortedCoinAmounts = Object.keys(coinAmounts).sort((a, b) => parseFloat(a) - parseFloat(b)).reduce((obj, key) => {
                obj[key] = coinAmounts[key];
                return obj;
            }, {});

            // Calculate the value of each coin and the total balance
            let totalBalance = 0;
            for (const coinValue in sortedCoinAmounts) {
                const amountOwned = sortedCoinAmounts[coinValue];
                const coin = coins.find(c => c.value == coinValue);
                const coinName = parseFloat(coinValue);
                const coinValueInEuros = coin ? coin.value : parseFloat(coinValue);
                const coinValueTotal = amountOwned * coinValueInEuros;
                totalBalance += coinValueTotal;

                // Add a row to the table for this coin
                const tr = document.createElement("tr");
                const nameTd = document.createElement("td");
                nameTd.innerText = coinName.toLocaleString("pt-PT", { style: "currency", currency: "EUR" });
                const amountTd = document.createElement("td");
                amountTd.innerText = amountOwned;
                const valueTd = document.createElement("td");
                valueTd.innerText = coinValueTotal.toLocaleString("pt-PT", { style: "currency", currency: "EUR" });
                tr.appendChild(nameTd);
                tr.appendChild(amountTd);
                tr.appendChild(valueTd);
                document.getElementById("coin-table").appendChild(tr);
            }

            // Set the total balance in the table footer
            document.getElementById("total-balance").innerText = totalBalance.toLocaleString("pt-PT", { style: "currency", currency: "EUR" });
        });
}

var depositButton = document.getElementById("deposit-button");
var modalDeposit = document.getElementById("deposit-modal");
var closeButtonDeposit = document.getElementsByClassName("close")[0];

depositButton.onclick = function() {
    modalDeposit.style.display = "block";
}

closeButtonDeposit.onclick = function() {
    modalDeposit.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == modalDeposit) {
        modalDeposit.style.display = "none";
    } else if (event.target == modalWithdrawl) {
        modalWithdrawl.style.display = "none";
    }
}

var requestSent = false;

$(function() {
    $('#deposit-form').submit(function(event) {
        if (!requestSent) {
            // Prevent default form submission behavior
            event.preventDefault();
            event.stopPropagation();
        
            // Get form data
            var formData = {
                'coin-deposit': $('#coin-deposit').val(),
                'amount-deposit': $('#amount-deposit').val()
            };
        
            // Send AJAX request to server
            $.ajax({
                type: 'POST',
                url: '/deposit/'+name_,
                data: formData,
                success: function(response) {
                    // Refresh the page
                    location.href = "/profile/" + name_;
                },
                error: function(xhr, status, error) {
                    // Handle error response
                    location.href = "/profile/" + name_;
                }
            });
        }
        requestSent = true;
    });
});


var withdrawlButton = document.getElementById("withdrawl-button");
var modalWithdrawl = document.getElementById("withdrawl-modal");
var closeButtonWithdrawl = document.getElementsByClassName("close")[1];

withdrawlButton.onclick = function() {
    modalWithdrawl.style.display = "block";
}

closeButtonWithdrawl.onclick = function() {
    modalWithdrawl.style.display = "none";
}

var requestSent_ = false;

$(function() {
    $('#withdrawl-form').submit(function(event) {
        if (!requestSent_) {
            // Prevent default form submission behavior
            event.preventDefault();
            event.stopPropagation();

            // Get form data
            var formData = {
                'coin-withdrawl': $('#coin-withdrawl').val(),
                'amount-withdrawl': $('#amount-withdrawl').val()
            };
        
            // Send AJAX request to server
            $.ajax({
                type: 'POST',
                url: '/withdrawl/'+name_,
                data: formData,
                success: function(response) {
                    // Refresh the page
                    location.href = "/profile/" + name_;
                },
                error: function(xhr, status, error) {
                    // Handle error response
                    location.href = "/profile/" + name_;
                }
            });
        }
        requestSent_ = true;
    });
});


var loanButton = document.getElementById("loan-button");
var modalLoan = document.getElementById("loan-modal");
var closeButtonLoan = document.getElementsByClassName("close")[2];

loanButton.onclick = function() {
    modalLoan.style.display = "block";
    // Get the calendar ID from the HTML and call loadEventsFromBackend
    const calendarId = id_; // Replace 'loan-modal' with the actual ID of your calendar div
    loadEventsFromBackend(calendarId);
}

closeButtonLoan.onclick = function() {
    modalLoan.style.display = "none";
}


// Load events from the backend
function loadEventsFromBackend(calendarId) {
    fetch(`/calendar/${calendarId}`)
    .then(response => response.json())
    .then(eventsData => {
        const events = [];
        
        // Convert the dictionary into an array of events
        for (const date in eventsData) {
            if (eventsData.hasOwnProperty(date)) {
            const formattedDate = moment(date, 'DD-MM-YYYY').format('YYYY-MM-DD');
            events.push({
                title: eventsData[date],
                start: formattedDate
            });
            }
        }
        
        // Initialize FullCalendar with the loaded events
        $(`#calendar`).fullCalendar({
            events: events,
            // Set other FullCalendar options and callbacks as needed
            eventClick: function(event) {
            const eventInfo = `
                <h3>${event.title}</h3>
                <p>${moment(event.start).format('DD-MM-YYYY')}</p>
            `;
            $('#event-info').html(eventInfo);
            }
        });
    })
    .catch(error => {
        console.error('Failed to load events from the backend:', error);
    });
}


function redirectToNewPage(username) {
    window.location.href = "/account/" + username;
}