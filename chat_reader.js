import { Innertube } from "youtubei.js";

const videoId = process.env.YT_VIDEO_ID;
if (!videoId) throw new Error("Missing YT_VIDEO_ID");
const log = (...args) => console.error("[CHAT]", ...args);

function textOf(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value.runs)) return value.runs.map(run => run?.text || run?.emoji?.shortcuts?.[0] || "").join("");
  if (typeof value.text === "string") return value.text;
  return "";
}

async function main() {
  log("Connecting to live chat for", videoId);
  const yt = await Innertube.create({ lang: "en", location: "IN" });
  const info = await yt.getInfo(videoId);
  const chat = info.getLiveChat();
  if (!chat) throw new Error("No live chat returned for this video. Confirm the YouTube event is live and chat is enabled.");

  chat.on("chat-update", action => {
    try {
      const item = action?.item;
      if (!item) return;
      const author = textOf(item.author?.name || item.author_name) || "Viewer";
      const author_id = String(item.author?.id || item.author?.channel_id || item.author?.channelId || item.author_id || "").trim()
        || (author !== "Viewer" ? "display-name:" + author.toLowerCase() : "");
      if (!author_id) return;
      const badges = JSON.stringify(item.author?.badges || item.author?.badge || []).toLowerCase();
      const is_moderator = Boolean(item.author?.is_moderator || item.author?.isModerator || badges.includes("moderator"));
      const avatar_url = item.author?.thumbnails?.[0]?.url || item.author?.thumbnail?.[0]?.url || "";
      // Do not forward or store chat message contents in analytics.
      process.stdout.write(JSON.stringify({ author, author_id, is_moderator, avatar_url, text: "" }) + "\n");
    } catch (err) {
      log("Skipped unparseable chat event:", err?.message || String(err));
    }
  });
  chat.on("error", err => log("Live chat error:", err?.message || String(err)));
  chat.on("start", () => log("Live chat connected."));
  chat.start();
  process.on("SIGTERM", () => { try { chat.stop(); } catch {} process.exit(0); });
  process.on("SIGINT", () => { try { chat.stop(); } catch {} process.exit(0); });
}
main().catch(err => { log("Unable to read chat:", err?.stack || String(err)); process.exit(1); });
