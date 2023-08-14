function previewFile() {
    var fileInput = document.getElementById('file');
    var preview = document.getElementById('preview');
    var fileIcon = document.getElementById('file-icon');
    var fileName = fileInput.files[0].name;
    var ext = fileName.split('.').pop().toLowerCase();
    var allowedExts = ['csv', 'xls', 'xlsx'];
    if (allowedExts.indexOf(ext) === -1) {
        preview.innerHTML = 'Por favor, selecione um arquivo Excel ou CSV.';
        fileIcon.src = '';
    } else if (allowedExts.indexOf(ext) === 1 || allowedExts.indexOf(ext) === 2) {
        preview.innerHTML = fileName;
        fileIcon.src = fileIcon.src = "../static/images/xls_icon.png";
    } else {
        preview.innerHTML = fileName;
        fileIcon.src = fileIcon.src = "../static/images/csv_icon.png";
    }
}


document.addEventListener("DOMContentLoaded", function() {
    fetch(`/dados_saldo/${id}`)
        .then(response => response.json())
        .then(data => {
            const datas = data.map(item => item.data);
            const saldos = data.map(item => parseFloat(item.saldo)); // Convert to numeric format

            const ctx = document.getElementById('grafico-saldo').getContext('2d');
            var chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: datas,
                    datasets: [{
                        label: 'Saldo (Eco)',
                        data: saldos,
                        backgroundColor: 'rgba(0, 123, 255, 0.5)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Data'
                            }
                        },
                        y: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Saldo (€)'
                            },
                            ticks: {
                                callback: function(value, index, values) {
                                    return value + ' €';
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    var label = context.dataset.label || '';

                                    if (label) {
                                        label += ': ';
                                    }
                                    label += context.formattedValue + ' €';

                                    return label;
                                }
                            }
                        }               
                    },
                    animation: {
                        duration: 1500,
                        onComplete: function(animation) {
                            const imageUrl = this.toBase64Image();
                            // Send the image URL to the server
                            fetch(`/save-graphic/${id}`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    imageUrl: imageUrl
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                console.log(data); // Handle the server response if needed
                            })
                            .catch(error => {
                                console.error('An error occurred:', error);
                            });
                        }
                    }
                }
            });
        });
});


function openPopup() {
    const popupContent = `
        <form id="upload-form" enctype="multipart/form-data">
            <a>Selecione um arquivo Excel ou CSV:</a>
            <br>
            <label for="file" id="file-label">Upload</label>
            <input type="file" name="file" id="file" accept=".csv, .xls, .xlsx" class="file-input" onchange="previewFile()">
            <br>
            <img src="" id="file-icon" style="margin-top: 15px;">
            <div id="preview"></div>
            <br>
            <input type="submit" value="Submeter" style="background: rgb(77, 155, 75); border-color: transparent; cursor: pointer;">
        </form>
    `;

    const popup = window.open('about:blank', 'popup', 'width=600,height=200');
    popup.document.open();
    popup.document.write(popupContent);
    popup.document.close();

    popup.document.getElementById('upload-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
    
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
            window.location.reload(); // Reload the parent window on success
            } else {
            console.error(data.message); // Handle error message if needed
            }
            popup.close(); // Close the popup window
        })
        .catch(error => {
            console.error('An error occurred:', error);
            popup.close(); // Close the popup window
        });
    });
}
