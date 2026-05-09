using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Musnews.Data;
using Musnews.Models;
using Musnews.Models.DTO;
using System.Security.Claims;

namespace Musnews.Server.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class TracksController : ControllerBase
{
    private readonly ITrackRepository _trackRepo;

    public TracksController(ITrackRepository trackRepo)
    {
        _trackRepo = trackRepo;
    }

    private int GetCurrentUserId()
    {
        return int.Parse(User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "0");
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var userId = GetCurrentUserId();
        var tracks = await _trackRepo.GetByUserIdAsync(userId);

        var trackDtos = tracks.Select(t => new TrackDto
        {
            Id = t.Id,
            Title = t.Title,
            Artist = t.Artist,
            Album = t.Album,
            DurationSec = t.DurationSec,
            AudioUrl = t.AudioUrl,
            UserId = t.UserId
        });

        return Ok(trackDtos);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var track = await _trackRepo.GetByIdAsync(id);

        if (track is null)
            return NotFound();

        if (track.UserId != GetCurrentUserId())
            return Forbid();

        return Ok(track);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] Track track)
    {
        track.UserId = GetCurrentUserId();

        await _trackRepo.AddAsync(track);
        return CreatedAtAction(nameof(GetById), new { id = track.Id }, track);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] Track track)
    {
        var existingTrack = await _trackRepo.GetByIdAsync(id);
        if (existingTrack is null)
            return NotFound();

        if (existingTrack.UserId != GetCurrentUserId())
            return Forbid();

        track.Id = id;
        track.UserId = GetCurrentUserId();
        await _trackRepo.UpdateAsync(track);
        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var track = await _trackRepo.GetByIdAsync(id);
        if (track is null)
            return NotFound();

        if (track.UserId != GetCurrentUserId())
            return Forbid();

        if (!string.IsNullOrEmpty(track.AudioUrl))
        {
            var filePath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", track.AudioUrl.TrimStart('/'));
            if (System.IO.File.Exists(filePath))
            {
                System.IO.File.Delete(filePath);
            }
        }

        await _trackRepo.DeleteAsync(id);
        return NoContent();
    }

    [HttpPost("{id}/audio")]
    public async Task<IActionResult> UploadAudio(int id, IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("Файл не выбран");

        var track = await _trackRepo.GetByIdAsync(id);
        if (track is null)
            return NotFound();

        if (track.UserId != GetCurrentUserId())
            return Forbid();

        var userId = GetCurrentUserId();
        var uploadsFolder = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "music", userId.ToString());

        if (!Directory.Exists(uploadsFolder))
            Directory.CreateDirectory(uploadsFolder);

        var fileName = $"{id}_{Path.GetFileName(file.FileName)}";
        var filePath = Path.Combine(uploadsFolder, fileName);

        using (var stream = new FileStream(filePath, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }

        track.AudioUrl = $"/music/{userId}/{fileName}";
        await _trackRepo.UpdateAsync(track);

        return Ok(new { url = track.AudioUrl });
    }
}