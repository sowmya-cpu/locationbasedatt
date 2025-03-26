$(document).ready(function() {
  // Global variables to hold captured image blobs
  var capturedSmileBlob = null;
  var capturedAngryBlob = null;
  var capturedVerifyBlob = null;
  
  // Start camera for a given video element
  function startCamera(videoElementId) {
    var video = document.getElementById(videoElementId);
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
      .then(function(stream) {
        video.srcObject = stream;
        video.play();
      })
      .catch(function(err) {
        console.error("Error accessing camera: ", err);
      });
    } else {
      alert("getUserMedia is not supported in this browser.");
    }
  }
  
  // Initialize both cameras
  startCamera('register-video');
  startCamera('verify-video');
  
  // Capture an image from video and return a blob and data URL
  function captureImage(videoId, canvasId, callback) {
    var video = document.getElementById(videoId);
    var canvas = document.getElementById(canvasId);
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    var context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(function(blob) {
      callback(blob, canvas.toDataURL());
    }, 'image/jpeg');
  }
  
  // Capture smile image
  $('#capture-smile').click(function() {
    captureImage('register-video', 'register-canvas', function(blob, dataUrl) {
      capturedSmileBlob = blob;
      $('#smile-preview').attr('src', dataUrl);
    });
  });
  
  // Capture angry image
  $('#capture-angry').click(function() {
    captureImage('register-video', 'register-canvas', function(blob, dataUrl) {
      capturedAngryBlob = blob;
      $('#angry-preview').attr('src', dataUrl);
    });
  });
  
  // Capture verification image
  $('#capture-verify').click(function() {
    captureImage('verify-video', 'verify-canvas', function(blob, dataUrl) {
      capturedVerifyBlob = blob;
      $('#verify-preview').attr('src', dataUrl);
    });
  });
  
  // Toggle between Register and Verify sections
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
  
  // AJAX submission for registration (without geolocation)
  $('#register-form').submit(function(e) {
    e.preventDefault();
    
    var username = $('#register-username').val().trim();
    if (!username) {
      alert("Please enter a username.");
      return;
    }
    if (!capturedSmileBlob || !capturedAngryBlob) {
      alert("Please capture both smile and angry images.");
      return;
    }
    
    var formData = new FormData();
    formData.append('username', username);
    formData.append('smile_image', capturedSmileBlob, 'smile.jpg');
    formData.append('angry_image', capturedAngryBlob, 'angry.jpg');
    
    $.ajax({
      url: '/register',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function(response) {
        $('#register-response').html('<p>' + response.message + '</p>');
      },
      error: function(xhr) {
        $('#register-response').html('<p>Error: ' + xhr.responseJSON.error + '</p>');
      }
    });
  });
  
  // AJAX submission for verification (with geolocation)
  $('#verify-form').submit(function(e) {
    e.preventDefault();
    
    var username = $('#verify-username').val().trim();
    if (!username) {
      alert("Please enter a username.");
      return;
    }
    if (!capturedVerifyBlob) {
      alert("Please capture the verification image.");
      return;
    }
    
    // Get the user's geolocation only for verification
    navigator.geolocation.getCurrentPosition(function(position) {
      var lat = position.coords.latitude;
      var lon = position.coords.longitude;
      console.log(lat)
      console.log(lon)
      
      var formData = new FormData();
      formData.append('username', username);
      formData.append('image', capturedVerifyBlob, 'verify.jpg');
      formData.append('lat', lat);
      formData.append('long', lon);
      
      $.ajax({
        url: '/verify',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
          $('#verify-response').html('<p>' + response.message + '</p>');
        },
        error: function(xhr) {
          $('#verify-response').html('<p>Error: ' + xhr.responseJSON.error + '</p>');
        }
      });
    }, function(error) {
      alert("Unable to retrieve your location. Error: " + error.message);
    });
  });
});
