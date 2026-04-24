using Microsoft.AspNetCore.Mvc;
using Musnews.Data;
using Musnews.Models;
using Musnews.Models.DTO;
using Microsoft.EntityFrameworkCore;

namespace Musnews.Server.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TracksController : ControllerBase
{
    private readonly ITrackRepository _trackRepo;

    public TracksController(ITrackRepository trackRepo)
    {
        _trackRepo = trackRepo;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var tracks = await _trackRepo.GetAllAsync();
        var trackDtos = tracks.Select(t => new TrackDto
        {
            Id = t.Id,
            Title = t.Title,
            Artist = t.Artist,
            Album = t.Album,
            DurationSec = t.DurationSec
        });
        return Ok(tracks);
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var track = await _trackRepo.GetByIdAsync(id);
        return track is null ? NotFound() : Ok(track);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] Track track)
    {
        await _trackRepo.AddAsync(track);
        return CreatedAtAction(nameof(GetById), new { id = track.Id }, track);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] Track track)
    {
        var existingTrack = await _trackRepo.GetByIdAsync(id);
        if (existingTrack is null) return NotFound();

        track.Id = id;
        await _trackRepo.UpdateAsync(track);
        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var track = await _trackRepo.GetByIdAsync(id);
        if (track is null) return NotFound();

        await _trackRepo.DeleteAsync(id);
        return NoContent();
    }

    [HttpPost("{id}/audio")]
    public async Task<IActionResult> UploadAudio(int id, IFormFile file)
    {
        if (file == null || file.Length == 0)
            return BadRequest("Файл не выбран");

        var track = await _trackRepo.GetByIdAsync(id);
        if (track is null) return NotFound();

        var uploadsFolder = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "music");
        if (!Directory.Exists(uploadsFolder))
            Directory.CreateDirectory(uploadsFolder);

        var fileName = $"{id}_{Path.GetFileName(file.FileName)}";
        var filePath = Path.Combine(uploadsFolder, fileName);

        using (var stream = new FileStream(filePath, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }

        track.AudioUrl = $"/music/{fileName}";
        await _trackRepo.UpdateAsync(track);

        return Ok(new { url = track.AudioUrl });
    }
}