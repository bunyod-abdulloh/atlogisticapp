document.addEventListener("DOMContentLoaded", function () {
    // Status o'zgarganda Telegram xabari haqida alert chiqarish
    const messageList = document.querySelector(".messagelist");

    if (messageList) {
        const items = messageList.querySelectorAll("li");

        items.forEach(function (item) {
            const text = item.textContent.trim();
            if (text) {
                alert(text);
            }
        });

        messageList.style.display = "none";
    }

    // Qidiruv maydoniga placeholder qo'shish
    const searchInput = document.getElementById("searchbar");

    if (searchInput) {
        searchInput.placeholder =
            "Track-raqam, mijoz ism sharifi yoki telefon raqami";
    }
});