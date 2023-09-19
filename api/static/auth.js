let captchaData;
let completedCaptcha = false;

document.addEventListener("DOMContentLoaded", function () {
  fetchCaptchaImages();
});

function toggleSelection(element) {
  element.classList.toggle("selected");
}

function populateCaptcha(data) {
  const container = document.getElementById("recaptcha-container");
  const title = document.getElementById("recaptcha-title");
  title.innerHTML = data.title;
  const oldRows = container.getElementsByClassName("recaptcha-row");
  while (oldRows.length > 0) {
    oldRows[0].parentNode.removeChild(oldRows[0]);
  }

  const images = data.questions;

  let rows = Math.ceil(images.length / 4);
  let htmlContent = "";
  for (let r = 0; r < rows; r++) {
    htmlContent += '<div class="recaptcha-row">';
    for (let i = 0; i < 4; i++) {
      const index = r * 4 + i;
      if (images[index]) {
        htmlContent += `
          <div class="recaptcha-image" style="background-image: url('${images[index].image}');" onclick="toggleSelection(this)">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                  <path d="M20.285 2l-1.272.02L6.72 15.466l-5.644-5.58L0 12.352l7.218 7.15L24 2.083z"/>
              </svg>
            </div>
        `;
      }
    }
    htmlContent += "</div>";
  }

  title.insertAdjacentHTML("afterend", htmlContent);
  captchaData = data;
  session_id = data.session_id;
}

async function verifyCaptcha(redirect_url) {
  const selectedImages = document.querySelectorAll(".recaptcha-image.selected");
  const answers = [];
  selectedImages.forEach((img) => {
    const backgroundImageURL = img.style.backgroundImage;
    const imageURL = backgroundImageURL.slice(5, backgroundImageURL.length - 2);
    answers.push(
      captchaData.questions.find((question) => question.image === imageURL).id
    );
  });
  const captchaAnswer = {
    session: captchaData.session,
    answer: answers.join(","),
  };
  try {
    const response = await fetch("https://vtuber-captcha.vercel.app/api/verify", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(captchaAnswer).toString(),
    });
    const data = await response.json();

    if (data.success) {
        window.location.href = redirect_url;
      
    } else {
      alert("Sorry, you failed the captcha. Please try again.")
      fetchCaptchaImages();
    }
  } catch (error) {
    console.error("Error verifying captcha:", error);
  }
}


function fetchCaptchaImages() {
  let options = ["Hololive", "Nijisanji"]
  let randomOption = options[Math.floor(Math.random() * options.length)];
  console.log(randomOption);
  fetch("https://vtuber-captcha.vercel.app/api/affiliation/"+randomOption+"?auth=server")
    .then((response) => response.json())
    .then((data) => {
      populateCaptcha(data);
    })
    .catch((error) => {
      console.error("There was an error fetching the captcha:", error);
    });
}
