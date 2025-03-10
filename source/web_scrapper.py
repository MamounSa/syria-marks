import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import List

import aiohttp
from telegram import Message

UNIVERSITY_URL = "https://exam.homs-univ.edu.sy/exam-it/re.php"


@dataclass
class WebStudentResponse:
    student_number: int
    html_page: bytes


async def multi_async_request(
    numbers: List[int], recurse_limit: int = 2, message: Message = None
) -> List[WebStudentResponse]:
    async with aiohttp.ClientSession() as session:
        processed = [0]
        total = [len(numbers)]
        current_time = [monotonic()]
        tasks =[
            asyncio.create_task(
                one_req(
                        int(number),
                        session,
                        recurse_limit,
                        update_progress_bar_message,
                        processed,
                        total,
                        message,
                        current_time
                    )
                )
            for number in numbers
        ]
        gathered = await asyncio.gather(*tasks)
    return gathered


async def one_req(
    number, session: aiohttp.ClientSession, recurse_limit: int,
    callback = None, processed = None, total = None, message: Message = None, last_update = None 
) -> WebStudentResponse:
    if recurse_limit <= 0:
        raise Exception("uncompleted request, try again later")

    try:
        async with session.post(UNIVERSITY_URL, data={"number1": number}) as req:
            res_data = await req.read()
        if req.status != 200:
            await asyncio.sleep(1)
            return await one_req(number, session, recurse_limit - 1)
        if callback:
            processed[0] += 1
            await callback(processed[0], total[0], message, last_update)
        return WebStudentResponse(number, res_data)
    except Exception:
        await asyncio.sleep(1)
        return await one_req(number, session, recurse_limit - 1)


progress_bar_length = 10
progress_bar_processed_icon = '◾️'
progress_bar_unprocessed_icon = '️▫️'


async def update_progress_bar_message(processed: int, total: int, message: Message, last_update: List[float]):
    if monotonic() - last_update[0] >= 1:
        last_update[0] = monotonic()
        progress = await calculate_progress(processed, total, progress_bar_length)
        progress_bar = await generate_progress_bar(progress, progress_bar_length) 
        await message.edit_text(
            reply_markup = message.reply_markup,
            text = f"⏳ يتم جلب المعلومات من الموقع ...\n\n{processed} / {total}\n  [{progress_bar}]"
        )
 
 
async def calculate_progress(processed: int, total: int, max_progress_value: int) -> int:
    if total < 0:
        raise Exception("Can't calculate progress for nigative number of processes!")
    if total == 0:
        return max_progress_value
    return int(processed / total * max_progress_value) 


async def generate_progress_bar(progress: int, max_progress_value: int) -> str:
    if progress < 0 or progress > max_progress_value:
        raise Exception("Can't generate progress bar for invalid progress value!")
    progress_bar = ''
    for i in range(1,progress + 1):
        progress_bar = progress_bar + progress_bar_processed_icon
    for i in range(progress + 1, max_progress_value + 1):
        progress_bar = progress_bar + progress_bar_unprocessed_icon
    return progress_bar