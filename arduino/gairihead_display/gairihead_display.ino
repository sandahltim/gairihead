/*
 * GairiHead TFT Display Controller
 *
 * Arduino Uno + 2.8" TP28017 TFT HAT (240x320)
 * Serial communication with Raspberry Pi 5
 *
 * Features:
 * - 3 display views: Conversation, Status, Debug
 * - Touch button interface
 * - Expression-to-emoji mapping
 * - Authorization level color coding
 * - JSON protocol over USB serial
 *
 * Uses MCUFRIEND_kbv library for 8-bit parallel interface
 * Serial RX buffer increased to 512 bytes in HardwareSerial.h
 */

#include <Adafruit_GFX.h>
#include <MCUFRIEND_kbv.h>
#include <TouchScreen.h>
#include <ArduinoJson.h>

// =============================================================================
// HARDWARE CONFIGURATION
// =============================================================================

// TFT uses 8-bit parallel interface (no CS/DC/RST defines needed)

// Touchscreen pins (TP28017 - Detected by diagnose_Touchpins)
#define YP A3  // Y+ (must be analog)
#define XM A2  // X- (must be analog)
#define YM 9   // Y-
#define XP 8   // X+

// Touchscreen calibration
#define TS_MINX 150
#define TS_MINY 120
#define TS_MAXX 920
#define TS_MAXY 940
#define MINPRESSURE 10
#define MAXPRESSURE 1000

// Display dimensions
#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 320

// =============================================================================
// OBJECTS
// =============================================================================

MCUFRIEND_kbv tft;  // Use MCUFRIEND for parallel interface
TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);

// =============================================================================
// COLORS
// =============================================================================

#define COLOR_BG       0x0000  // Black
#define COLOR_TEXT     0xFFFF  // White
#define COLOR_TITLE    0x07FF  // Cyan
#define COLOR_USER     0x07E0  // Green
#define COLOR_GAIRI    0x07FF  // Cyan
#define COLOR_BUTTON   0x4208  // Dark gray
#define COLOR_AUTH_1   0x07E0  // Green (Level 1 - Tim)
#define COLOR_AUTH_2   0xFFE0  // Yellow (Level 2 - Authorized)
#define COLOR_AUTH_3   0xF800  // Red (Level 3 - Stranger)
#define COLOR_EXPR     0xFBE0  // Orange (Expression)

// =============================================================================
// DISPLAY MODES
// =============================================================================

enum DisplayView {
  VIEW_CONVERSATION,
  VIEW_STATUS,
  VIEW_DEBUG
};

DisplayView currentView = VIEW_CONVERSATION;

// Conversation pagination (0 = user question, 1 = Gairi response)
int conversationPage = 1;  // Start on Gairi response (most recent)

// =============================================================================
// TOUCH BUTTON STRUCTURE
// =============================================================================

struct TouchButton {
  int x, y, w, h;
  String action;
};

// =============================================================================
// STATE VARIABLES
// =============================================================================

// Conversation data
String userText = "";
String gairiText = "";
String expression = "idle";
String tier = "local";
float responseTime = 0.0;

// Status data
String userName = "Unknown";
int authLevel = 3;
String systemState = "idle";
float confidence = 0.0;

// Debug data
String lastTool = "none";
bool trainingLogged = false;

// Touch handling
unsigned long lastTouchTime = 0;
const unsigned long touchDebounce = 500; // ms

// Serial buffer
String serialBuffer = "";
const unsigned int maxBufferSize = 1024;

// =============================================================================
// EXPRESSION TO EMOJI MAPPING
// =============================================================================

String expressionToEmoji(String expr) {
  if (expr == "happy") return F(":)");
  if (expr == "amused") return F(":D");
  if (expr == "sarcasm") return F(";)");
  if (expr == "deadpan") return F(":|");
  if (expr == "unimpressed") return F("-_-");
  if (expr == "disapproval") return F(":/");
  if (expr == "calculating") return F("o.O");
  if (expr == "thinking") return F("...");
  if (expr == "processing") return F("*_*");
  if (expr == "alert") return F("!");
  if (expr == "concern") return F(":(");
  if (expr == "concerned") return F(":(");
  if (expr == "frustrated") return F(">:(");
  if (expr == "confused") return F("???");
  if (expr == "sheepish") return F("^_^;");
  if (expr == "pride") return F("^_^");
  if (expr == "celebration") return F("\\o/");
  if (expr == "listening") return F("o.o");
  if (expr == "idle") return F("-.-");
  if (expr == "neutral") return F(":|");
  if (expr == "intrigued") return F("o.o");
  if (expr == "surprised") return F("O_O");
  if (expr == "skeptical") return F("-_-");
  if (expr == "bored") return F("-_-");
  return F("^_^");
}

// =============================================================================
// TEXT WRAPPING UTILITY
// =============================================================================

void wrapText(String text, int x, int y, int maxWidth, int lineHeight, uint16_t color) {
  tft.setTextColor(color);
  tft.setTextSize(2);  // Increased size for better readability

  int cursorX = x;
  int cursorY = y;
  String word = "";

  for (unsigned int i = 0; i < text.length(); i++) {
    char c = text.charAt(i);

    if (c == ' ' || c == '\n' || i == text.length() - 1) {
      // Add last character if end of string
      if (i == text.length() - 1 && c != ' ' && c != '\n') {
        word += c;
      }

      // Measure word width
      int16_t x1, y1;
      uint16_t w, h;
      tft.getTextBounds(word.c_str(), 0, 0, &x1, &y1, &w, &h);

      // Check if word fits on current line
      if (cursorX + w > x + maxWidth) {
        // Move to next line
        cursorX = x;
        cursorY += lineHeight;

        // Check if we're past screen bottom
        if (cursorY > SCREEN_HEIGHT - lineHeight) {
          return; // Stop drawing
        }
      }

      // Draw word
      tft.setCursor(cursorX, cursorY);
      tft.print(word);
      cursorX += w + 6; // Add space width

      word = "";

      // Handle newline
      if (c == '\n') {
        cursorX = x;
        cursorY += lineHeight;
      }
    } else {
      word += c;
    }
  }
}

// =============================================================================
// BUTTON DRAWING
// =============================================================================

void drawButton(int x, int y, int w, int h, String label, uint16_t bgColor, uint16_t textColor) {
  tft.fillRoundRect(x, y, w, h, 5, bgColor);
  tft.drawRoundRect(x, y, w, h, 5, textColor);

  // Center text in button
  int16_t x1, y1;
  uint16_t tw, th;
  tft.setTextSize(1);
  tft.getTextBounds(label.c_str(), 0, 0, &x1, &y1, &tw, &th);

  tft.setCursor(x + (w - tw) / 2, y + (h - th) / 2);
  tft.setTextColor(textColor);
  tft.print(label);
}

// =============================================================================
// TOUCH DETECTION
// =============================================================================

// Touch buttons at bottom
TouchButton btnLeft = {10, 280, 70, 35, "View"};
TouchButton btnCenter = {85, 280, 70, 35, "Action"};
TouchButton btnRight = {160, 280, 70, 35, "View"};

bool isTouchInButton(TSPoint p, TouchButton btn) {
  // Map touch coordinates to screen coordinates
  int px = map(p.x, TS_MINX, TS_MAXX, 0, SCREEN_WIDTH);
  int py = map(p.y, TS_MINY, TS_MAXY, 0, SCREEN_HEIGHT);

  return (px >= btn.x && px <= btn.x + btn.w &&
          py >= btn.y && py <= btn.y + btn.h);
}

// =============================================================================
// VIEW: CONVERSATION (PAGINATED)
// =============================================================================

// Page 0: User Question View
void drawUserQuestionView() {
  tft.fillScreen(COLOR_BG);

  // Title with page indicator
  tft.setTextSize(2);
  tft.setTextColor(COLOR_USER);
  tft.setCursor(10, 10);
  tft.print("User Question");

  // Page indicator
  tft.setTextSize(1);
  tft.setTextColor(COLOR_AUTH_2);
  tft.setCursor(SCREEN_WIDTH - 50, 15);
  tft.print("(1/2)");

  // Expression emoji
  tft.setTextSize(2);
  tft.setTextColor(COLOR_EXPR);
  tft.setCursor(SCREEN_WIDTH - 60, 35);
  tft.print(expressionToEmoji(expression));

  // User text (much more vertical space now!)
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  wrapText(userText, 10, 70, SCREEN_WIDTH - 20, 18, COLOR_TEXT);

  // Listening indicator (show if in listening state)
  if (systemState == "listening") {
    // Show prominent mic indicator
    tft.setTextSize(2);
    tft.setTextColor(COLOR_EXPR);
    tft.setCursor(10, 200);
    tft.print("MIC LISTENING...");

    tft.setTextSize(1);
    tft.setTextColor(COLOR_AUTH_2);
    tft.setCursor(10, 225);
    tft.print("Speak now");
  }

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Demo", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// Page 1: Gairi Response View
void drawGairiResponseView() {
  tft.fillScreen(COLOR_BG);

  // Title with page indicator
  tft.setTextSize(2);
  tft.setTextColor(COLOR_GAIRI);
  tft.setCursor(10, 10);
  tft.print("Gairi Response");

  // Page indicator
  tft.setTextSize(1);
  tft.setTextColor(COLOR_AUTH_2);
  tft.setCursor(SCREEN_WIDTH - 50, 15);
  tft.print("(2/2)");

  // Expression emoji
  tft.setTextSize(2);
  tft.setTextColor(COLOR_EXPR);
  tft.setCursor(SCREEN_WIDTH - 60, 35);
  tft.print(expressionToEmoji(expression));

  // Gairi text (much more vertical space now!)
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  wrapText(gairiText, 10, 70, SCREEN_WIDTH - 20, 18, COLOR_TEXT);

  // Footer info
  tft.setTextSize(1);
  tft.setTextColor(COLOR_AUTH_2);
  tft.setCursor(10, 250);
  tft.print("Tier: ");
  tft.print(tier);
  tft.print("  Time: ");
  tft.print(responseTime, 2);
  tft.print("s");

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Demo", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// Main conversation view dispatcher
void drawConversationView() {
  if (conversationPage == 0) {
    drawUserQuestionView();
  } else {
    drawGairiResponseView();
  }
}

// =============================================================================
// VIEW: STATUS
// =============================================================================

void drawStatusView() {
  tft.fillScreen(COLOR_BG);

  // Title
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(10, 10);
  tft.print("Status");

  // User info with auth level color
  uint16_t authColor = COLOR_AUTH_3;
  if (authLevel == 1) authColor = COLOR_AUTH_1;
  else if (authLevel == 2) authColor = COLOR_AUTH_2;

  tft.setTextSize(2);
  tft.setTextColor(authColor);
  tft.setCursor(10, 50);
  tft.print("User: ");
  tft.print(userName);

  tft.setTextSize(1);
  tft.setCursor(10, 75);
  tft.print("Auth Level: ");
  tft.print(authLevel);

  // System state
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 110);
  tft.print("State:");

  tft.setTextSize(1);
  tft.setCursor(10, 135);
  tft.setTextColor(COLOR_EXPR);
  tft.print(systemState);
  tft.print(" (");
  tft.print(expression);
  tft.print(")");

  // Show listening indicator if in listening state
  if (systemState == "listening") {
    tft.setTextSize(2);
    tft.setTextColor(COLOR_EXPR);
    tft.setCursor(150, 110);
    tft.print("MIC");
  }

  // Confidence
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 170);
  tft.print("Confidence:");

  tft.setTextSize(1);
  tft.setCursor(10, 195);
  int confPercent = (int)(confidence * 100);
  tft.print(confPercent);
  tft.print("%");

  // Confidence bar
  int barWidth = (int)(200 * confidence);
  tft.drawRect(10, 210, 200, 20, COLOR_TEXT);
  tft.fillRect(11, 211, barWidth, 18, authColor);

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Guest", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// =============================================================================
// VIEW: DEBUG
// =============================================================================

void drawDebugView() {
  tft.fillScreen(COLOR_BG);

  // Title
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(10, 10);
  tft.print("Debug Info");

  // LLM Tier
  tft.setTextSize(1);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 50);
  tft.print("LLM Tier: ");
  tft.setTextColor(tier == "local" ? COLOR_AUTH_1 : COLOR_AUTH_2);
  tft.print(tier);

  // Last tool
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 80);
  tft.print("Last Tool:");
  tft.setCursor(10, 95);
  tft.setTextColor(COLOR_EXPR);
  tft.print(lastTool);

  // Training status
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 125);
  tft.print("Training Logged: ");
  tft.setTextColor(trainingLogged ? COLOR_AUTH_1 : COLOR_AUTH_3);
  tft.print(trainingLogged ? "YES" : "NO");

  // Response time
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 155);
  tft.print("Response Time:");
  tft.setCursor(10, 170);
  tft.setTextColor(COLOR_EXPR);
  tft.print(responseTime, 3);
  tft.print(" seconds");

  // Expression
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 200);
  tft.print("Expression: ");
  tft.setTextColor(COLOR_EXPR);
  tft.print(expression);
  tft.print(" ");
  tft.setTextSize(2);
  tft.print(expressionToEmoji(expression));

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Demo", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// =============================================================================
// VIEW SWITCHING
// =============================================================================

void switchView(DisplayView newView) {
  currentView = newView;

  switch (currentView) {
    case VIEW_CONVERSATION:
      drawConversationView();
      break;
    case VIEW_STATUS:
      drawStatusView();
      break;
    case VIEW_DEBUG:
      drawDebugView();
      break;
  }
}

void nextView() {
  switch (currentView) {
    case VIEW_CONVERSATION:
      switchView(VIEW_STATUS);
      break;
    case VIEW_STATUS:
      switchView(VIEW_DEBUG);
      break;
    case VIEW_DEBUG:
      switchView(VIEW_CONVERSATION);
      break;
  }
}

void previousView() {
  switch (currentView) {
    case VIEW_CONVERSATION:
      switchView(VIEW_DEBUG);
      break;
    case VIEW_STATUS:
      switchView(VIEW_CONVERSATION);
      break;
    case VIEW_DEBUG:
      switchView(VIEW_STATUS);
      break;
  }
}

// =============================================================================
// JSON MESSAGE HANDLING
// =============================================================================

void handleJsonMessage(String json) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, json);

  if (error) {
    Serial.print(F("{\"error\":\"parse\",\"code\":\""));
    Serial.print(error.c_str());
    Serial.println(F("\"}"));
    return;
  }

  const char* type = doc["type"];

  if (strcmp(type, "conversation") == 0) {
    // Extract conversation data
    const char* userTextPtr = doc["user_text"];
    const char* gairiTextPtr = doc["gairi_text"];

    userText = (userTextPtr != nullptr) ? String(userTextPtr) : "";
    gairiText = (gairiTextPtr != nullptr) ? String(gairiTextPtr) : "";
    expression = doc["expression"].as<String>();
    tier = doc["tier"] | "local";
    responseTime = doc["response_time"] | 0.0;

    // Auto-switch to conversation view and display
    switchView(VIEW_CONVERSATION);

  } else if (strcmp(type, "status") == 0) {
    userName = doc["user"].as<String>();
    authLevel = doc["level"] | 3;
    systemState = doc["state"].as<String>();
    confidence = doc["confidence"] | 0.0;
    expression = doc["expression"].as<String>();

    // Redraw current view to show state changes (especially listening indicator)
    if (currentView == VIEW_STATUS) {
      drawStatusView();
    } else if (currentView == VIEW_CONVERSATION && conversationPage == 0) {
      // Redraw user question view to show listening indicator
      drawUserQuestionView();
    }

    Serial.println(F("{\"ok\":1}"));

  } else if (strcmp(type, "debug") == 0) {
    tier = doc["tier"].as<String>();
    lastTool = doc["tool"].as<String>();
    trainingLogged = doc["training_logged"] | false;
    responseTime = doc["response_time"] | 0.0;

    if (currentView == VIEW_DEBUG) {
      drawDebugView();
    }

    Serial.println(F("{\"ok\":1}"));

  } else {
    Serial.println(F("{\"error\":\"type\"}"));
  }
}

// =============================================================================
// TOUCH HANDLING
// =============================================================================

void handleTouch() {
  TSPoint p = ts.getPoint();

  // Need to reset pins for TFT after touch reading
  pinMode(XM, OUTPUT);
  pinMode(YP, OUTPUT);

  // Check if valid touch
  if (p.z < MINPRESSURE || p.z > MAXPRESSURE) {
    return;
  }

  // Debounce
  unsigned long currentTime = millis();
  if (currentTime - lastTouchTime < touchDebounce) {
    return;
  }
  lastTouchTime = currentTime;

  // Check which button was pressed
  if (isTouchInButton(p, btnLeft)) {
    Serial.println(F("{\"touch\":\"left\"}"));

    // If in conversation view, cycle conversation pages
    if (currentView == VIEW_CONVERSATION) {
      conversationPage = (conversationPage == 0) ? 1 : 0;
      drawConversationView();
    } else {
      previousView();
    }

  } else if (isTouchInButton(p, btnRight)) {
    Serial.println(F("{\"touch\":\"right\"}"));

    // If in conversation view, cycle conversation pages
    if (currentView == VIEW_CONVERSATION) {
      conversationPage = (conversationPage == 0) ? 1 : 0;
      drawConversationView();
    } else {
      nextView();
    }

  } else if (isTouchInButton(p, btnCenter)) {
    Serial.println(F("{\"touch\":\"center\"}"));
    // Reserved for future actions (voice trigger)
  }
}

// =============================================================================
// SETUP
// =============================================================================

void setup() {
  // Initialize serial
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port
  }

  // Print configuration
  Serial.print(F("{\"device\":\"GairiHead Display\",\"display\":\""));
  uint16_t ID = tft.readID();
  Serial.print(ID, HEX);
  Serial.println(F("\",\"touch\":\"TP28017\",\"status\":\"ready\"}}"));

  tft.begin(ID);
  tft.setRotation(0);
  tft.fillScreen(COLOR_BG);

  // Welcome message
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(30, 140);
  tft.print(F("GairiHead"));

  delay(1000);

  // Show initial view
  switchView(VIEW_CONVERSATION);

  // Send ready signal
  Serial.println(F("{\"ok\":1}"));
}

// =============================================================================
// MAIN LOOP
// =============================================================================

void loop() {
  // Handle serial input
  // Wait for complete message to arrive in buffer
  if (Serial.available() > 0) {
    delay(20);  // Allow full message to arrive in buffer
  }

  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      // Complete message received
      if (serialBuffer.length() > 0) {
        handleJsonMessage(serialBuffer);
        serialBuffer = "";
      }
    } else {
      // Add to buffer
      serialBuffer += c;

      // Prevent buffer overflow
      if (serialBuffer.length() >= maxBufferSize) {
        Serial.println(F("{\"error\":\"buf\"}"));
        serialBuffer = "";
      }
    }
  }

  // Handle touch input
  handleTouch();

  // Small delay - keep short for fast serial processing
  delay(10);
}
