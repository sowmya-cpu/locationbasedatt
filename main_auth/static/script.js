$(document).ready(function() {
  // ----- Tab switching -----
  $('#show-register').click(function() {
    $('#register-section').show();
    $('#verify-section').hide();
    $('.tab-button').removeClass('active');
    $(this).addClass('active');
  });
  $('#show-verify').click(function() {
    $('#register-section').hide();
    $('#verify-section').show();
    $('.tab-button').removeClass('active');
    $(this).addClass('active');
  });

  // ----- Open Cam: Register -----
  const openCamButton = document.getElementById('open-cam');
  const registerContainer = document.getElementById('webcam-container');
  const registerVideo     = document.getElementById('register-video');
  let registerStream;

  openCamButton.addEventListener('click', function(e) {
    e.preventDefault();
    openCamButton.style.display = 'none';
    registerContainer.style.display = 'block';
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        registerStream = stream;
        registerVideo.srcObject = stream;
      })
      .catch(err => console.error('Error accessing register cam:', err));
  });

  // ----- Open Cam: Verify -----
  const openCamVerifyButton   = document.getElementById('open-cam-verify');
  const verifyContainer       = document.getElementById('webcam-container-verify');
  const verifyVideo           = document.getElementById('verify-video');
  let verifyStream;

  openCamVerifyButton.addEventListener('click', function(e) {
    e.preventDefault();
    openCamVerifyButton.style.display = 'none';
    verifyContainer.style.display = 'block';
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        verifyStream = stream;
        verifyVideo.srcObject = stream;
      })
      .catch(err => console.error('Error accessing verify cam:', err));
  });

  // ----- Capture & Preview Logic -----
  let capturedSmileBlob  = null;
  let capturedAngryBlob  = null;
  let capturedVerifyBlob = null;

  function captureImage(videoEl, canvasEl, cb) {
    const video  = document.getElementById(videoEl);
    const canvas = document.getElementById(canvasEl);
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(blob => cb(blob, canvas.toDataURL()), 'image/jpeg');
  }

  $('#capture-smile').click(() =>
    captureImage('register-video','register-canvas', (b, url) => {
      capturedSmileBlob = b;
      $('#smile-preview').attr('src', url);
    })
  );

  $('#capture-angry').click(() =>
    captureImage('register-video','register-canvas', (b, url) => {
      capturedAngryBlob = b;
      $('#angry-preview').attr('src', url);
    })
  );

  $('#capture-verify').click(() =>
    captureImage('verify-video','verify-canvas', (b, url) => {
      capturedVerifyBlob = b;
      $('#verify-preview').attr('src', url);
    })
  );

  // ----- AJAX Form Submissions -----
  const BASE = window.location.origin;

  $('#register-form').submit(function(e) {
    e.preventDefault();
    const username = $('#register-username').val().trim();
    if (!username) return alert("Please enter a username.");
    if (!capturedSmileBlob || !capturedAngryBlob)
      return alert("Capture both smile and angry images.");

    const fd = new FormData();
    fd.append('username', username);
    fd.append('smile_image',  capturedSmileBlob, 'smile.jpg');
    fd.append('angry_image',  capturedAngryBlob, 'angry.jpg');

    $.ajax({
      url:         BASE + '/register/',
      type:        'POST',
      data:        fd,
      processData: false,
      contentType: false,
      success(res) {
        $('#register-response').html(
          `<p style="color:green">${res.message}</p>`
        );
      },
      error(xhr) {
        const msg = xhr.responseJSON?.error || xhr.statusText;
        $('#register-response').html(
          `<p style="color:red">Error: ${msg}</p>`
        );
      }
    });
  });

  $('#verify-form').submit(function(e) {
    e.preventDefault();
    const username = $('#verify-username').val().trim();
    if (!username) return alert("Please enter a username.");
    if (!capturedVerifyBlob) return alert("Please capture the verification image.");
    if (!navigator.geolocation) return alert("Geolocation not supported.");

    navigator.geolocation.getCurrentPosition(pos => {
      const fd = new FormData();
      fd.append('username', username);
      fd.append('image', capturedVerifyBlob, 'verify.jpg');
      fd.append('lat', pos.coords.latitude);
      fd.append('long', pos.coords.longitude);

      $.ajax({
        url:         BASE + '/verify/',
        type:        'POST',
        data:        fd,
        processData: false,
        contentType: false,
        success(res) {
          $('#verify-response').html(
            `<p style="color:green">${res.message}</p>`
          );
        },
        error(xhr) {
          if (xhr.status === 403) {
            // instead of injecting the JSON error into the page...
            alert('You are not in the specified location.');
          } else {
            // handle other errors as before
            const msg = xhr.responseJSON?.error || xhr.statusText;
            $('#verify-response').html(
              `<p style="color:red">Error: ${msg}</p>`
            );
          }
        }
      });
    });
  });
});
