import OpenAI from "openai";
import { NextRequest, NextResponse } from "next/server";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const completion = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages,
  });
  return NextResponse.json({ reply: completion.choices[0].message.content });
}
