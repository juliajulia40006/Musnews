using Microsoft.AspNetCore.Mvc;
using Musnews.Data;
using Musnews.Models;

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
}
