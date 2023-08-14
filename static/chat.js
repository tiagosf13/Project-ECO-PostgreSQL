var socketio = io();
const messages = document.getElementById("messages");

socketio.on("message", (data) => {
    createMessage(data.time, data.name, data.message, data.image);
});

socketio.on("disconnect", () => {
    socketio.emit("disconnect", { place: "chat" });
});

const createMessage = (time, name, msg, imgSrc) => {
    console.log(time, name, msg, imgSrc);
    const isCurrentUser = currentUser == name;
    console.log(isCurrentUser);
    const messageClass = isCurrentUser ? 'current-user' : '';

    const senderImageClass = isCurrentUser ? `sender-image-${messageClass}` : `sender-image`;

    const imgElement = `<img src="${imgSrc}" alt="${name}'s image" class="${senderImageClass}">`;
    const nameElement = `${name}`;
    const senderContent = isCurrentUser ? `${nameElement}${imgElement}` : `${imgElement}${nameElement}`;
    const senderClass = isCurrentUser ? `sender-${messageClass}` : `sender`;

    const mutedClass = isCurrentUser ? `muted-${messageClass}` : `muted`;
    const textClass = isCurrentUser ? `text-${messageClass}` : `text`;

    const content = `
        <div class="${messageClass}">
            <div class="${senderClass}">
                ${senderContent}
            </div>
            <div class="${textClass}">${msg.replace(/\n/g, "<br>")}</div>
            <div class="${mutedClass}">${time}</div>
            <br>
        </div>
    `;
    messages.insertAdjacentHTML("beforeend", content);
    messages.scrollTop = messages.scrollHeight;
};



const sendMessage = (id_, name_) => {
    const message = document.getElementById("message");
    if (message.value == "") return;
    socketio.emit("message", { name: id_, message: message.value });
    message.value = "";
};

var messageInput = document.getElementById("message");
var id = messageInput.getAttribute("data-id");
var username = messageInput.getAttribute("data-name");
messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage(id, username);
    } else if (event.key === "Enter" && event.shiftKey) {
        event.preventDefault();
        event.target.value += "\r\n";
    }
});


const scrollToBottom = () => {
    messages.scrollTop = messages.scrollHeight;
    document.getElementById('scroll-to-bottom').style.display = 'none';
};
